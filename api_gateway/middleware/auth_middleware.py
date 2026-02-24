from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api_gateway.authentication.api.security import validate_jwt_token


def require_auth(request: Request):

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing Authorization header"},
        )

    token = auth_header.split(" ")[1]
    try:
        payload = validate_jwt_token(token)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"},
        )
    # 

    request.state.user_id = payload.get("sub")
    request.state.type = payload.get("type")
