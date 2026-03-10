import hashlib
from uuid import uuid4, UUID
from typing import List
from datetime import datetime, timezone
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api_gateway.authentication.api.security import validate_jwt_token
from api_gateway.settings import settings
from shared_database.repository import APIKeyService, UserRepository
from shared_database.connection import SessionLocal, get_db

from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

security = HTTPBearer(auto_error=False)

class AuthUser:

    def __init__(self, user_id:str, auth_type: str, scopes: List[str] = []):
        self.user_id = user_id
        self.auth_type = auth_type
        self.scopes = scopes

        

class VerificationService:

    def __init__(self, db: Session):
        self.db = db
        self.api_repo = APIKeyService(db)
        self.user_repo = UserRepository(db)
     
    def verify_api_key(self, token: str) -> AuthUser:
        

        hashed_token = self._hash_token(token)
        key_record = self.api_repo.get_by_key(hashed_key=hashed_token)

        if not key_record:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
        
        if key_record.expiring_at < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API Key expired")

        if not key_record.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key has been revoked")
        
        print(key_record)
        
        return AuthUser(user_id=str(key_record.user_id), auth_type="api_key")
    
    def verify_jwt_token(self, token:str) -> AuthUser:

        try:
            payload = validate_jwt_token(token)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid jwt or expired token"},
            )

        user_id = payload.get("sub")
        user = self.user_repo.get_by_id(user_id=user_id)

        if not user.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User not exists or not active")
        
        return AuthUser(
            user_id=str(user.id),
            auth_type="jwt"
        )

    def _hash_token(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()


class DualAuthMiddleware:

    PUBLIC_PATHS = {"/", 
                    "/docs", 
                    "/redoc", 
                    "/openapi.json", 
                    "/favicon.ico",
                    "/health", 
                    "/metrics",
                    "/google/login",
                    "/login",
                    "/signup",
                    "/verify-password",
                    "/github/login",
                    "/google/callback",
                    "/github/callback"
                }
    
    

    def __init__(self, app):
        self.app = app


    async def __call__(self, scope, receive, send):

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return 
        
        request = Request(scope, receive, send)

        if request.url.path in self.PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return
        
        response = await self._resolve(request)
        
        if response:
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)

    async def _resolve(self,request: Request):
        raw = request.headers.get("Authorization", "")
        scheme, token = get_authorization_scheme_param(raw)

        if not raw or scheme.lower() != 'bearer' or not token:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Authorization header missing or malformed. Expected: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )
        db = SessionLocal()

        try:
            service = VerificationService(db)
            if token.startswith(settings.API_KEY_PREFIX):
                request.state.user = service.verify_api_key(token)
            else:
                request.state.user = service.verify_jwt_token(token)

            return None

        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )

        finally:
            db.close()
            

        
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AuthUser:
    
    user = getattr(request.state, 'user', None)

    if user:
        return user
    
    if not credentials:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    
    token = credentials.credentials

    if token.startswith(settings.API_KEY_PREFIX):
        request.state.user = VerificationService(db).verify_api_key(token)
    else:
        request.state.user = VerificationService(db).verify_jwt_token(token)


def require_scopes(scope: str):
    async def _guard(user: AuthUser = Depends(get_current_user)):
        if scope not in user.scope


        


