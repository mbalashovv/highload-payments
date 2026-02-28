from fastapi import FastAPI

from highload_payments.apps.api.http.routes import router
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import ApiSettings, load_api_settings


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    app_settings = settings or load_api_settings()

    configure_logging(level=app_settings.common.log_level)
    app = FastAPI(title=f"{app_settings.common.app_name} API")
    app.include_router(router)
    return app


app = create_app()
