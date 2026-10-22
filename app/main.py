from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.admin import build_admin
from app.api import health
from app.api.v1.router import api_router
from app.api.v1.routes import debtors
from app.core.config import Settings, get_settings
from app.core.database import make_engine
from app.core.exceptions import register_exception_handlers
from app.web.routes import router as web_router

STATIC_DIR = Path(__file__).parent / "web" / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine, sessionmaker = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Учёт оплат",
        version="1.0.0",
        description="Мини-учёт оплат учебного центра: ученики, оплаты, должники за месяц.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.sessionmaker = sessionmaker
    register_exception_handlers(app)

    app.include_router(api_router)
    app.include_router(debtors.router, include_in_schema=False)
    app.include_router(health.router)
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    build_admin(engine, settings).mount_to(app)
    return app


app = create_app()
