from fastapi import FastAPI

from highload_payments.apps.api.http.routes import router
from highload_payments.infrastructure.observability.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Highload Payments API")
    app.include_router(router)
    return app


app = create_app()

