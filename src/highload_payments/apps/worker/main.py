import asyncio
import logging

from highload_payments.apps.worker.bootstrap import build_publish_outbox_use_case
from highload_payments.apps.worker.jobs.publish_outbox import publish_once
from highload_payments.infrastructure.db.session import create_db_runtime
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import load_worker_settings


async def run() -> None:
    settings = load_worker_settings()
    configure_logging(level=settings.common.log_level)
    db_runtime = create_db_runtime(settings.db)
    try:
        use_case = build_publish_outbox_use_case(
            settings=settings,
            session_factory=db_runtime.session_factory,
        )
        logger = logging.getLogger(__name__)

        while True:
            processed = await publish_once(use_case, batch_size=settings.worker.batch_size)
            if processed == 0:
                await asyncio.sleep(settings.worker.poll_interval_seconds)
            else:
                logger.info("published outbox events: %s", processed)
    finally:
        await db_runtime.dispose()


if __name__ == "__main__":
    asyncio.run(run())
