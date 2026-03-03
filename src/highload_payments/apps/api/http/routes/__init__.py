from fastapi import FastAPI

from highload_payments.apps.api.http.routes.health import health_router
from highload_payments.apps.api.http.routes.payments import payments_router

__all__ = ["setup_controllers"]


def setup_controllers(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(payments_router)
