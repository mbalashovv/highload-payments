import asyncio

from highload_payments.apps.dispatcher.bootstrap import build_deliver_webhook_use_case
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import load_dispatcher_settings


async def run() -> None:
    settings = load_dispatcher_settings()
    configure_logging(level=settings.common.log_level)

    _ = build_deliver_webhook_use_case(settings=settings)
    while True:
        await asyncio.sleep(settings.dispatcher.poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run())
