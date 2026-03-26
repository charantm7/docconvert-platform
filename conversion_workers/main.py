import asyncio
from conversion_workers.queue.rabbitmq import init_rabbitmq
from conversion_workers.queue.consumer import start_consumer


async def main():
    connection, channel, retry_exchange, dlx_exchange = await init_rabbitmq()
    await start_consumer(connection, channel, retry_exchange, dlx_exchange)


if __name__ == "__main__":
    asyncio.run(main())
