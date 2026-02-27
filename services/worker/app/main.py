import asyncio
import json
import logging
import signal
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from .config import Settings

settings = Settings.from_env()
logger = logging.getLogger(settings.app_name)
logging.basicConfig(level=settings.log_level.upper())

PROCESSING_TIME = Histogram("worker_processing_seconds", "Time spent processing tasks")
PROCESSED = Counter("worker_processed_total", "Total processed tasks")
FAILED = Counter("worker_failed_total", "Total failed tasks")


class TaskMessage(BaseModel):
    task_id: str
    payload: dict[str, Any]


class WorkerState:
    def __init__(self) -> None:
        self.stop_event = asyncio.Event()
        self.consumer: AIOKafkaConsumer | None = None
        self.valkey: redis.Redis | None = None
        self.consume_task: asyncio.Task | None = None


state = WorkerState()


async def _get_valkey() -> redis.Redis:
    return redis.Redis(
        host=settings.valkey_host,
        port=settings.valkey_port,
        password=settings.valkey_password,
        db=settings.valkey_db,
        decode_responses=True,
    )


async def _process_message(body: bytes) -> None:
    with PROCESSING_TIME.time():
        task = TaskMessage.model_validate_json(body)
        await asyncio.sleep(settings.simulate_work_ms / 1000)
        result = {
            "task_id": task.task_id,
            "payload": task.payload,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": 2,
        }
        assert state.valkey is not None
        await state.valkey.set(f"result:{task.task_id}", json.dumps(result))
        await state.valkey.incr("stats:processed_total")
        backlog = await state.valkey.decr("stats:queue_backlog")
        if backlog < 0:
            await state.valkey.set("stats:queue_backlog", 0)
        PROCESSED.inc()


async def _consume() -> None:
    assert state.consumer is not None
    await state.consumer.start()
    try:
        async for message in state.consumer:
            try:
                await _process_message(message.value)
                await state.consumer.commit()
            except Exception:
                FAILED.inc()
                logger.exception("Failed processing message")
    except KafkaError:
        logger.exception("Kafka consumer error")
    finally:
        await state.consumer.stop()


async def _shutdown():
    state.stop_event.set()
    if state.consume_task:
        try:
            await asyncio.wait_for(state.consume_task, timeout=settings.shutdown_grace_seconds)
        except asyncio.TimeoutError:
            logger.warning("Shutdown timed out, forcing close")
    if state.consumer:
        await state.consumer.stop()
    if state.valkey:
        await state.valkey.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.valkey = await _get_valkey()
    state.consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        max_poll_records=settings.prefetch_count,
        security_protocol="SASL_PLAINTEXT",
        sasl_mechanism="PLAIN",
        sasl_plain_username=settings.kafka_username,
        sasl_plain_password=settings.kafka_password,
    )
    state.consume_task = asyncio.create_task(_consume())
    yield
    await _shutdown()


app = FastAPI(title="Worker", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    if state.consumer is None or state.valkey is None:
        return {"status": "starting"}
    return {"status": "ready"}


def _install_signal_handlers():
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(_shutdown()))


_install_signal_handlers()
