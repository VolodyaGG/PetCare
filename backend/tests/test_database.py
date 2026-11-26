import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import Settings, get_settings
from app.main import create_app

pytestmark = pytest.mark.integration


def test_postgres_migration_round_trip_and_readiness(monkeypatch):
    # Only an explicit test URL is accepted: never downgrade a developer's normal database.
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    engine = create_engine(url)
    config = Config("alembic.ini")
    try:
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version"))
        command.check(config)
        command.downgrade(config, "base")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM alembic_version")) == 0
        command.upgrade(config, "head")
        with TestClient(create_app(Settings(database_url=url))) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["database"] == "ok"
    finally:
        engine.dispose()
        get_settings.cache_clear()
