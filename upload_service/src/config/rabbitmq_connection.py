import aio_pika

from upload_service.settings import settings


async def get_rabbit_connection():
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)
