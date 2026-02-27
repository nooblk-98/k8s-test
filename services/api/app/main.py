import json
import logging
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import jwt
import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from .config import Settings

settings = Settings.from_env()
logger = logging.getLogger(settings.app_name)
logging.basicConfig(level=settings.log_level.upper())


class TaskRequest(BaseModel):
    payload: dict[str, Any]
    task_id: str | None = None


class StatsResponse(BaseModel):
    valkey_keys: int
    queue_backlog: int
    processed_count: int


REQUESTS = Counter("api_requests_total", "Total API requests", ["endpoint", "method", "status"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "API request latency", ["endpoint", "method"])


async def _get_valkey() -> redis.Redis:
    return redis.Redis(
        host=settings.valkey_host,
        port=settings.valkey_port,
        password=settings.valkey_password,
        db=settings.valkey_db,
        decode_responses=True,
    ) 


async def _require_jwt(authorization: str | None = Header(default=None)) -> None:
    if not settings.jwt_required:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    try:
        jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.valkey = await _get_valkey()
    app.state.producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        security_protocol="SASL_PLAINTEXT",
        sasl_mechanism="PLAIN",
        sasl_plain_username=settings.kafka_username,
        sasl_plain_password=settings.kafka_password,
    )
    await app.state.producer.start()
    yield
    await app.state.producer.stop()
    await app.state.valkey.close()


app = FastAPI(title="API Gateway", lifespan=lifespan)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    endpoint = request.url.path
    method = request.method
    with REQUEST_LATENCY.labels(endpoint=endpoint, method=method).time():
        response = await call_next(request)
    REQUESTS.labels(endpoint=endpoint, method=method, status=str(response.status_code)).inc()
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    try:
        await app.state.valkey.ping()
        if app.state.producer.partitions_for(settings.kafka_topic) is None:
            raise HTTPException(status_code=503, detail="Kafka metadata unavailable")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Dependencies not ready") from exc
    return {"status": "ready"}


@app.post("/task", dependencies=[Depends(_require_jwt)])
async def enqueue_task(task: TaskRequest):
    task_id = task.task_id or str(uuid4())
    payload = {"task_id": task_id, "payload": task.payload}
    body = json.dumps(payload).encode("utf-8")

    try:
        await app.state.producer.send_and_wait(settings.kafka_topic, body)
        await app.state.valkey.incr("stats:queue_backlog")
    except KafkaError as exc:
        logger.exception("Failed to publish task")
        raise HTTPException(status_code=503, detail="Queue unavailable") from exc

    return {"status": "queued", "task_id": task_id}


@app.get("/stats", response_model=StatsResponse, dependencies=[Depends(_require_jwt)])
async def stats():
    try:
        valkey_keys = await app.state.valkey.dbsize()
        processed_raw = await app.state.valkey.get("stats:processed_total")
        processed_count = int(processed_raw or 0)
        backlog_raw = await app.state.valkey.get("stats:queue_backlog")
        queue_backlog = max(int(backlog_raw or 0), 0)
    except Exception as exc:
        logger.exception("Failed to gather stats")
        raise HTTPException(status_code=503, detail="Stats unavailable") from exc

    return StatsResponse(
        valkey_keys=valkey_keys,
        queue_backlog=queue_backlog,
        processed_count=processed_count,
    )
