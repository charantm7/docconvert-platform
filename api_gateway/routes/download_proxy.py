import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..settings import settings

dowload = APIRouter()


@dowload.api_route("/download/{path:path}", methods=["GET"])
async def proxy_download(path: str, request: Request):

    forward_header = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {
            "host",
            "connection"
        }
    }

    forward_header["User-Id"] = request.state.user_id
    forward_header["Request-Id"] = request.state.request_id

    async with httpx.AsyncClient(timeout=None) as client:
        upstream = await client.stream(
            "GET",
            f"{settings.DOWNLOAD_SERVICE_URL}/download/{path}",
            headers=forward_header
        )

    return StreamingResponse(
        upstream.aiter_raw(),
        status_code=upstream.status_code,
        headers={
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in {
                "connection",
                "transfer-encoding",
                "content-length"

            }
        }

    )
