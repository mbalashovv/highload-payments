from contextlib import asynccontextmanager

from fastapi import FastAPI

from highload_payments.apps.api.http.routes import router
from highload_payments.infrastructure.db.session import create_db_runtime
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import ApiSettings, load_api_settings


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    app_settings = settings or load_api_settings()
    db_runtime = create_db_runtime(app_settings.db)
    configure_logging(level=app_settings.common.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db_runtime = db_runtime
        yield
        await db_runtime.dispose()

    app = FastAPI(title=f"{app_settings.common.app_name} API", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
