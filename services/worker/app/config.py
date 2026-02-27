import os
from pydantic import BaseModel


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_name: str = "worker"
    log_level: str = "info"
    kafka_bootstrap_servers: str
    kafka_topic: str = "tasks"
    kafka_username: str
    kafka_password: str
    kafka_group_id: str = "worker-group"
    valkey_host: str = "valkey-master.infrastructure.svc.cluster.local"
    valkey_port: int = 6379
    valkey_password: str | None = None
    valkey_db: int = 0
    prefetch_count: int = 10
    shutdown_grace_seconds: int = 20
    simulate_work_ms: int = 200

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "worker"),
            log_level=os.getenv("LOG_LEVEL", "info"),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.infrastructure.svc.cluster.local:9092"),
            kafka_topic=os.getenv("KAFKA_TOPIC", "tasks"),
            kafka_username=os.getenv("KAFKA_USERNAME", "app"),
            kafka_password=os.getenv("KAFKA_PASSWORD", "change-me"),
            kafka_group_id=os.getenv("KAFKA_GROUP_ID", "worker-group"),
            valkey_host=os.getenv("VALKEY_HOST", "valkey-master.infrastructure.svc.cluster.local"),
            valkey_port=int(os.getenv("VALKEY_PORT", "6379")),
            valkey_password=os.getenv("VALKEY_PASSWORD"),
            valkey_db=int(os.getenv("VALKEY_DB", "0")),
            prefetch_count=int(os.getenv("PREFETCH_COUNT", "10")),
            shutdown_grace_seconds=int(os.getenv("SHUTDOWN_GRACE_SECONDS", "20")),
            simulate_work_ms=int(os.getenv("SIMULATE_WORK_MS", "200")),
        )
