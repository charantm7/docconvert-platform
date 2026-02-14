
import httpx
from fastapi import APIRouter, Request, Response, Depends
from api_gateway.middleware.auth_middleware import require_auth

from ..settings import settings

upload = APIRouter(dependencies=[Depends(require_auth)])


@upload.post("/upload/presigned")
async def proxy_presigned_generation_upload(request: Request):

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
    forward_header["Request-Id"] = request.state.request_id

    json_body = await request.json()

    async with httpx.AsyncClient(timeout=10) as client:
        upstream_response = await client.post(
            url=f"{settings.UPLOAD_SERVICE_URL}/upload/presigned",
            headers=forward_header,
            json=json_body
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


@upload.api_route("/upload/{path:path}", methods=["GET", "POST"])
async def proxy_presigned_generation_upload(path: str, request: Request):

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
    forward_header["Request-Id"] = request.state.request_id

    json_body = await request.json()

    async with httpx.AsyncClient(timeout=10) as client:
        upstream_response = await client.request(
            method=request.method,
            url=f"{settings.UPLOAD_SERVICE_URL}/{path}",
            headers=forward_header,
            json=json_body
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
