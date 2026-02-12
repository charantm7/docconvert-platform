import json
import aio_pika
from fastapi import APIRouter, HTTPException, Header, status

from upload_service.src.api.v1.upload_route.schema import PreSignedSchema, ConvertRequest
from upload_service.src.api.v1.upload_route.service import build_storage_path
from upload_service.src.config.rabbitmq_connection import get_rabbit_connection
from upload_service.src.storage.supabase_client import supabase

from upload_service.settings import settings

upload_service = APIRouter()


@upload_service.post("/upload/presigned")
async def generate_presigned_url(
    body: PreSignedSchema,
    user_id: str = Header(..., alias="User-Id")
):
    if not body.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename Required")

    file_path, job_id = build_storage_path(
        user_id=user_id, filename=body.filename)

    try:

        signed = supabase.storage.from_(
            settings.SUPABASE_BUCKET).create_signed_upload_url(file_path)
    except Exception as e:
        raise HTTPException(500, f"Supabase error: {str(e)}")

    return {
        "upload_url": signed["signedUrl"],
        "path": file_path,
        "job_id": job_id,
        "bucket": settings.SUPABASE_BUCKET
    }


@upload_service.post("/conversion/start")
async def convert_file(body: ConvertRequest):

    connection = await get_rabbit_connection()
    channel = await connection.channel()

    queue = await channel.declare_queue("conversion_queue", durable=True)

    message = {
        "job_id": body.job_id,
        "path": body.path,
        "target_format": body.target_format
    }

    await channel.default_exchange.publish(
        aio_pika.message(
            body=json.dumps(message).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=queue.name
    )

    await connection.close()

    return {"message": "Conversion job queued", "job_id": body.job_id}
