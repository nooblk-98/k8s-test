import os
from pydantic import BaseModel


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_name: str = "api"
    log_level: str = "info"
    kafka_bootstrap_servers: str
    kafka_topic: str = "tasks"
    kafka_username: str
    kafka_password: str
    valkey_host: str = "valkey-master.infrastructure.svc.cluster.local"
    valkey_port: int = 6379
    valkey_password: str | None = None
    valkey_db: int = 0
    jwt_secret: str = ""
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_required: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "api"),
            log_level=os.getenv("LOG_LEVEL", "info"),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.infrastructure.svc.cluster.local:9092"),
            kafka_topic=os.getenv("KAFKA_TOPIC", "tasks"),
            kafka_username=os.getenv("KAFKA_USERNAME", "app"),
            kafka_password=os.getenv("KAFKA_PASSWORD", "change-me"),
            valkey_host=os.getenv("VALKEY_HOST", "valkey-master.infrastructure.svc.cluster.local"),
            valkey_port=int(os.getenv("VALKEY_PORT", "6379")),
            valkey_password=os.getenv("VALKEY_PASSWORD"),
            valkey_db=int(os.getenv("VALKEY_DB", "0")),
            jwt_secret=os.getenv("JWT_SECRET", ""),
            jwt_issuer=os.getenv("JWT_ISSUER"),
            jwt_audience=os.getenv("JWT_AUDIENCE"),
            jwt_required=_bool(os.getenv("JWT_REQUIRED"), True),
        )
