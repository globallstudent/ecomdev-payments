from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import text
from testcontainers.community.postgres import PostgresContainer

from app.core.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def settings() -> Iterator[Settings]:
    with PostgresContainer("postgres:18-alpine", driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        config = Config(ROOT / "alembic.ini", toml_file=ROOT / "pyproject.toml")
        config.attributes["database_url"] = url
        command.upgrade(config, "head")
        yield Settings(database_url=url, secret_key="test-secret", app_timezone="Asia/Tashkent")


@pytest.fixture(scope="session")
async def app(settings: Settings) -> AsyncGenerator[FastAPI]:
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
    async with app.state.sessionmaker() as session:
        await session.execute(text("TRUNCATE payments, students RESTART IDENTITY CASCADE"))
        await session.commit()
