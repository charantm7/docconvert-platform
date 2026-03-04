from datetime import datetime, timezone
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api_gateway.authentication.api.security import validate_jwt_token
from api_gateway.settings import settings
from shared_database.repository import APIKeyService
import hashlib

from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

class VerificationService:

    def __init__(self, db: Session):
        self.db = db
        self.api_repo = APIKeyService(db)
     
    async def _verify_api_key(self, token: str):
        

        hashed_token = self._hash_token(token)
        key_record = self.api_repo.get_by_key(hashed_key=hashed_token)

        if not key_record:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
        
        if key_record.expiring_at < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API Key expired")

        if not key_record.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key has been revoked")
        
        return key_record.user_id
    
    def require_auth(self, token:str) -> str:

        try:
            payload = validate_jwt_token(token)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid jwt or expired token"},
            )

        request.state.user_id = payload.get("sub")
        request.state.type = payload.get("type")


    def _hash_token(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()








class DualAuthMiddleware:

    PUBLIC_PATHS = {"/", "/docs", "/redoc", "/openapi.json", "/health"}

    def __init__(self, app, db: Session):
        self.app = app
        self.db = db


    async def __call__(self, scope, receive, send):

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return 
        
        request = Request(scope, receive, send)

        if request.url.path in self.PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return
        
        try:
            request.state.user = 

            pass

    async def _resolve(self,request: Request):
        raw = request.headers.get("Authorization", "")
        scheme, token = get_authorization_scheme_param(raw)

        if not raw or scheme.lower() != 'bearer' or not token:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Authorization header missing or malformed. Expected: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if token.startswith(settings.API_KEY_PREFIX):
            return VerificationService(self.db)._verify_api_key(token)
        else:
            return 

        

        


