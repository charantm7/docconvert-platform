from uuid import uuid4
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from common_logging.request_context import request_id_ctx


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id

        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["Request-ID"] = request_id
        return response
