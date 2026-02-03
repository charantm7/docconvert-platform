from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from api_gateway.authentication.api.security import validate_jwt_token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request,  call_next):

        if request.url.path in ["/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header"
            )

        token = auth_header.split(" ")[1]
        payload = validate_jwt_token(token)

        request.state.user_id = payload.get("sub")
        request.state.type = payload.get("type")
        request.state.role = payload.get("role")

        return await call_next(request)
