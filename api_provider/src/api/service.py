import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Session
import logging

from shared_database.repository import APIKeyService
from api_provider.src.api.schema import APITokenResponseSchema, APICreationSchema


logger = logging.getLogger(__name__)
API_KEY_PREFIX = 'sk-'

class APIService:

    def __init__(self, user_id:str, db:Session):
        self.user_id = user_id
        self.db = db
        self.api_repo = APIKeyService(db)

    def create_new_token(self,data: APICreationSchema)-> str:

        if data.expire_at is None:
            data.expire_at = datetime.now(timezone.utc) + timedelta(days=30)

        token = API_KEY_PREFIX + self._token_generator()

        hashed_token = self._hash_token(token)

        record = self.api_repo.create(
            hashed_key=hashed_token,
            prefix=hashed_token[:10],
            name=data.name,
            expiring_at=data.expire_at,
            user_id=self.user_id,
            is_active=True,
            scopes=[s.value for s in data.scopes]
        )

        return APITokenResponseSchema(
            token=token, 
            id=str(record.id), 
            expire_at=record.expiring_at, 
            name=record.name,
            scopes=record.scopes
        )
    
    # ================
    # Internal Helpers
    # ===============

    def _token_generator(self)-> str:
        return secrets.token_urlsafe(32)
    
    def _hash_token(self, data: str)-> str:
        return hashlib.sha256(data.encode()).hexdigest()

