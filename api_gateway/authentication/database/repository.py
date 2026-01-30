import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api_gateway.authentication.database.models import AuthProviders, User, EmailVerificationToken, PasswordResetToken


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

    def get_by_username(self, username: str) -> User | None:
        exc = select(User).where(User.username == username)
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
        user.is_email_verified = True
        self.db.commit()

    def update_email_verification_sent_at(self, user: User) -> None:
        user.email_verification_sent_at = datetime.now(timezone.utc)
        self.db.commit()

    def update_email_verified_at(self, user_id: uuid.UUID) -> None:
        user = self.get_by_id(user_id)
        user.email_verified_at = datetime.now(timezone.utc)
        self.db.commit()

    def update_password(self, user: User, hashed_password: str) -> None:
        user.hashed_password = hashed_password
        self.db.commit()

    def update_password_reset_link_sent_at(self, user: User) -> None:
        user.password_reset_sent_at = datetime.now(timezone.utc)
        self.db.commit()

    def update_password_reseted_at(self, user: User) -> None:
        user.password_reseted_at = datetime.now(timezone.utc)
        self.db.commit()

    # Password Token record

    def create_password_reset_record(self, **fields) -> None:
        record = PasswordResetToken(**fields)
        self.db.add(record)
        self.db.commit()

    def is_password_reset_token_exists(self, token: str) -> PasswordResetToken:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.hashed_token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_password_reset_token_status(self, token_record: PasswordResetToken) -> None:
        token_record.used = True
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
