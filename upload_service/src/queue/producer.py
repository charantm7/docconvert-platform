import json
import aio_pika
from upload_service.src.config.rabbitmq_connection import get_rabbit_connection
from upload_service.settings import settings


class Queue:

    async def __init__(self):
        self.connection = await get_rabbit_connection()
        self.channel = await self.connection.channel()

    async def main_queue(self, message):

        main_exchange = await self.channel.declare_exchange("main_exchange", durable=True)

        queue = await self.channel.declare_queue(
            settings.CONVERSION_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "retry_exchange"
            }
        )

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue.name
        )

        await self.connection.close()

    async def retry_queue(self, message):
        retry_exchange = await self.channel.declare_exchange("retry_exchange", durable=True)

        queue = await self.channel.declare_queue(
            "retry_queue",
            durable=True,
            arguments={
                "x-message-ttl": 5000,
                "x-dead-letter-exchange": "main_exchange"
            }
        )
