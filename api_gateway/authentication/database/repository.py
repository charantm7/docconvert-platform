import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api_gateway.authentication.database.models import AuthProviders, User, EmailVerificationToken


class UserRepository:

    """
    Repository layer for user model,
    Handles all database interaction related to users
    """

    def __init__(self, db: Session):
        self.db = db

    # Queries

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        exc = select(User).where(User.email == email)
        return self.db.execute(exc).scalar_one_or_none()

    # Commands

    def create(self, **fields) -> User:
        user = User(**fields)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def exists_by_email(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email)
        return self.db.execute(stmt).first() is not None

    def update_last_login(
        self,
        provider: str,
        user: User
    ) -> None:
        user.last_loggin_at = datetime.now(timezone.utc)
        user.last_login_provider = provider
        self.db.commit()

    def update_email_verification_status(self, user_id: uuid.UUID) -> None:
        user = self.get_by_id(user_id)
        user.is_verified = True
        self.db.commit()


class EmailRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **fields) -> None:
        token = EmailVerificationToken(**fields)
        self.db.add(token)
        self.db.commit()

    def is_token_exists(self, hashed_token: str) -> EmailVerificationToken:
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.hashed_token == hashed_token)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_token_record_status(self, record: EmailVerificationToken) -> None:
        record.used = True
        self.db.commit()
