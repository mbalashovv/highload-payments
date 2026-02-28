import asyncio

from highload_payments.apps.dispatcher.bootstrap import build_deliver_webhook_use_case
from highload_payments.infrastructure.db.session import create_db_runtime
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import load_dispatcher_settings


async def run() -> None:
    settings = load_dispatcher_settings()
    configure_logging(level=settings.common.log_level)
    db_runtime = create_db_runtime(settings.db)

    try:
        _ = build_deliver_webhook_use_case(
            settings=settings,
            session_factory=db_runtime.session_factory,
        )
        while True:
            await asyncio.sleep(settings.dispatcher.poll_interval_seconds)
    finally:
        await db_runtime.dispose()


if __name__ == "__main__":
    asyncio.run(run())
