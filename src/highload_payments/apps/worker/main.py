import asyncio
import logging

from highload_payments.apps.worker.bootstrap import build_publish_outbox_use_case
from highload_payments.apps.worker.jobs.publish_outbox import publish_once


async def run() -> None:
    use_case = build_publish_outbox_use_case()
    logger = logging.getLogger(__name__)

    while True:
        processed = await publish_once(use_case, batch_size=100)
        if processed == 0:
            await asyncio.sleep(0.5)
        else:
            logger.info("published outbox events: %s", processed)


if __name__ == "__main__":
    asyncio.run(run())

