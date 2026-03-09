import httpx
from fastapi import APIRouter, Depends, Request, Response
from api_gateway.middleware.auth_middleware import get_current_user
from api_gateway.settings import settings


api_provider = APIRouter(dependencies=[Depends(get_current_user)])


@api_provider.api_route("/api/{path:path}", methods=["GET", "POST"])
async def api_provider_route_proxy(path: str, request: Request):

    forward_header = {
        key: value
        for key, value in request.headers.items()
        if key not in {
            "host",
            "content-length",
            "connection",
            "transfer-encoding"
        }
    } 


    forward_header["User-Id"] = request.state.user.user_id
    forward_header["Request-Id"] = request.state.request_id

    json_body = await request.json()

    async with httpx.AsyncClient(timeout=10) as client:
        upstream_response = await client.request(
            method=request.method,
            url=f"{settings.API_PROVIDER_SERVICE_URL}/{path}",
            headers=forward_header,
            json=json_body
        )

    return Response(
        status_code=upstream_response.status_code,
        content=upstream_response.content,
        headers={
            key:value
            for key, value in upstream_response.headers.items()
            if key not in {
                "content-length",
                "connection",
                "transfer-encoding"
            }
        },
        media_type=upstream_response.headers.get("content-type")
    )





