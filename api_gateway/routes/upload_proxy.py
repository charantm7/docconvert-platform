import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..settings import settings

upload = APIRouter()


@upload.api_route("/upload/{path:path}", methods=["GET", "POST"])
async def proxy_upload(path: str, request: Request):

    # filter the header
    forward_header = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {
            "host",
            "content-length",
            "connection"
        }
    }

    forward_header["User-Id"] = request.state.user_id
    forward_header["User-Role"] = request.state.role
    forward_header["Request-Id"] = request.state.request_id

    async def request_stream():
        async for chunk in request.stream():
            yield chunk

    async with httpx.AsyncClient(timeout=None) as client:
        upstream_response = await client.stream(
            method=request.method,
            url=f"{settings.UPLOAD_SERVICE_URL}/upload/{path}",
            headers=forward_header,
            content=request_stream()
        )

    return StreamingResponse(
        upstream_response.aiter_raw(),
        status_code=upstream_response.status_code,
        headers={
            key: value
            for key, value in upstream_response.headers.items()
            if key.lower() not in [
                "content-length",
                "connection",
                "transfer-encoding"
            ]
        }
    )
