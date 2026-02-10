
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

from ..settings import settings

upload = APIRouter()


@upload.post("/upload/presigned")
async def proxy_upload(request: Request):

    forward_header = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {
            "host",
            "content-length",
            "connection",
            "transfer-encoding",
        }
    }
    forward_header["User-Id"] = request.state.user_id
    forward_header["User-Role"] = request.state.role
    forward_header["Request-Id"] = request.state.request_id

    body = await request.body()

    async with httpx.AsyncClient(timeout=10) as client:
        upstream_response = await client.post(
            url=f"{settings.UPLOAD_SERVICE_URL}/upload/presigned",
            headers=forward_header,
            content=body
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers={
            key: value
            for key, value in upstream_response.headers.items()
            if key not in {
                "content-length",
                "connection",
                "transfer-encoding",
            }
        },
        media_type=upstream_response.headers.get("content-type")
    )
