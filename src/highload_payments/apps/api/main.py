from contextlib import asynccontextmanager

from fastapi import FastAPI

from highload_payments.apps.api.bootstrap import build_create_payment_use_case
from highload_payments.apps.api.http.routes import setup_controllers
from highload_payments.infrastructure.db.session import create_db_runtime
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import ApiSettings, load_api_settings


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    app_settings = settings or load_api_settings()
    db_runtime = create_db_runtime(app_settings.db)
    configure_logging(level=app_settings.common.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = app_settings
        app.state.db_runtime = db_runtime
        app.state.create_payment_use_case = build_create_payment_use_case(
            app_settings,
            db_runtime.session_factory,
        )
        yield
        await db_runtime.dispose()

    app = FastAPI(title=f"{app_settings.common.app_name} API", lifespan=lifespan)
    setup_controllers(app)
    return app


app = create_app()
