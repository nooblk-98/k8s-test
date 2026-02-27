import os
from app.config import Settings


def test_settings_defaults():
    os.environ.pop("KAFKA_BOOTSTRAP_SERVERS", None)
    settings = Settings.from_env()
    assert settings.kafka_topic == "tasks"
    assert settings.valkey_port == 6379
