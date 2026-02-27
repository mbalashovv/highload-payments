import asyncio

from highload_payments.apps.dispatcher.bootstrap import build_deliver_webhook_use_case


async def run() -> None:
    _ = build_deliver_webhook_use_case()
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())

