import asyncio
import json
import aio_pika

from conversion_workers.storage.s3_client import supabase
from conversion_workers.settings import settings
from conversion_workers.converter.worker import Conversion, Compression, Customization
from shared_database.connection import SessionLocal


async def start_consumer():

    print("[worker] Connecting to RabbitMQ...")

    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    channel = await connection.channel()

    queue = await channel.declare_queue(settings.QUEUE_NAME, durable=True)

    print(f"[worker] waiting for conversion job...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                db = SessionLocal()
                try:
                    data = json.loads(message.body)

                    user_id = data["user_id"]
                    job_id = data["job_id"]
                    path = data["path"]
                    target_format = data["target_format"]

                    print(f'[worker] recieved job id {job_id}')

                    if target_format == "docx":
                        Conversion(supabase, db).convert_pdf_to_docx(
                            job_id, path, user_id)

                    elif target_format == "pdf":
                        Conversion(supabase, db).convert_docx_to_pdf(
                            job_id, path, user_id)

                    elif target_format == "pptx":
                        Conversion(supabase, db).convert_pdf_to_ppt(
                            job_id, path, user_id)

                    elif target_format == "merge":
                        Customization(supabase).merge_pdf(
                            job_id, path, user_id)

                    elif target_format == "compress":
                        Compression(supabase).compress_pdf(
                            job_id, path, user_id)

                    else:
                        raise ValueError("Unsupported Formate")

                    print(f"[worker] finished job {job_id}")

                except Exception as e:
                    print(f"[Worker] Job failed: {e}")
                    raise
