import json
import aio_pika
from upload_service.src.config.rabbitmq_connection import get_rabbit_connection
from upload_service.settings import settings

connection = None
channel = None
main_exchange = None


async def init_rabbitmq():

    global connection, channel, main_exchange

    connection = await get_rabbit_connection()
    channel = await connection.channel()

    main_exchange = await channel.declare_exchange("main_exchange", durable=True)


async def publish_job(message: dict):
    await main_exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                **message,
                "retry_count": 0
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key="main"
    )
