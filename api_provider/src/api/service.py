import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Session
import logging

from shared_database.repository import APIKeyService


logger = logging.getLogger(__name__)
API_KEY_PREFIX = 'sk-'

class APIService:

    def __init__(self, user_id:str, db:Session):
        self.user_id = user_id
        self.db = db
        self.api_repo = APIKeyService(db)

    def create_new_token(self, name:str, expire_at: DateTime = datetime.now(timezone.utc) + timedelta(days=30) )-> str:

        token = API_KEY_PREFIX + self._token_generator()

        hashed_token = self._hash_token(token)

        self.api_repo.create(
            hashed_key=hashed_token,
            prefix=hashed_token[:10],
            name=name,
            expiring_at=expire_at,
            user_id=self.user_id,
            is_active=True
        )

        return token
    
    # ================
    # Internal Helpers
    # ===============

    def _token_generator(self)-> str:
        return secrets.token_urlsafe(32)
    
    def _hash_token(self, data: str)-> str:
        return hashlib.sha256(data.encode()).hexdigest()

