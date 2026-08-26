from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.common.handlers import register_exception_handlers
from app.core.config import get_settings
from app.db import registry as db_registry  # noqa: F401 - import registers audit listeners
from app.db.seeds.platform_admin import seed_platform_admin_from_settings


@asynccontextmanager
async def _seed_platform_admin_on_startup(_app: FastAPI) -> AsyncIterator[None]:
    await seed_platform_admin_from_settings(get_settings())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    is_production = settings.app_env == "production"
    app = FastAPI(
        title="Lensora API",
        lifespan=_seed_platform_admin_on_startup,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_router)

    return app


app = create_app()
