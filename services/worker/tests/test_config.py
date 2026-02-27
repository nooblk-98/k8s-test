from app.config import Settings


def test_worker_settings_defaults():
    settings = Settings.from_env()
    assert settings.kafka_topic == "tasks"
    assert settings.prefetch_count == 10
