import asyncio
from conversion_workers.queue.consumer import start_consumer

if __name__ == "__main__":
    asyncio.run(start_consumer())
