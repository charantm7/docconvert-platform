import json
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from api_gateway.authentication.api.security import (
    create_access_token,
    create_email_verification_token,
    create_password_hash,
    hash_token,
    validate_jwt_token,
    verify_password_hash,
    oauth2_scheme
)
from api_gateway.authentication.api.tasks import send_email_verification_link
from api_gateway.authentication.database.connection import get_db
from api_gateway.authentication.database.models import AuthProviders, User
from api_gateway.authentication.database.repository import EmailRepository, UserRepository
from api_gateway.authentication.api.schema import SignupSchema, LoginSchema
from api_gateway.settings import settings


class AuthService:

    """
    Service layer for Authentication
    Handles all the business logic
    """

    def __init__(self, db):
        self.repo = UserRepository(db)
        self.email_service = EmailService(db)

    def signup(self, data: SignupSchema, background_tasks: BackgroundTasks) -> str:
        self._ensure_email_not_taken(data.email)
        user = self._create_user(
            data,
            primary_provider=AuthProviders.LocalAuthentication,
            last_login_provider=AuthProviders.LocalAuthentication,
            last_login_at=datetime.now(timezone.utc)
        )

        background_tasks.add_task(
            self.email_service.create_and_send_email_verification,
            user
        )
        return self._issue_token(user)

    def login(self, data: LoginSchema) -> str:

        user = self.repo.get_by_email(data.email)
        self._ensure_user_availability_and_verify_password(
            user=user, data=data)
        self.repo.update_last_login(
            provider=AuthProviders.LocalAuthentication,
            user=user
        )
        return self._issue_token(user)

    # Internal helpers

    def _ensure_email_not_taken(self, email: str) -> None:
        if self.repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

    def _create_user(
            self,
            data: SignupSchema,
            primary_provider: AuthProviders,
            last_login_at: datetime,
            last_login_provider: AuthProviders
    ) -> User:

        payload = data.model_dump(exclude={"password", "confirm_password"})
        payload.update(
            {
                "hashed_password": create_password_hash(data.password),
                "primary_provider": primary_provider,
                "last_login_at": last_login_at,
                "last_login_provider": last_login_provider
            }
        )
        return self.repo.create(**payload)

    def _issue_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id))

    def _ensure_user_availability_and_verify_password(self, user: User, data: LoginSchema) -> None:
        if not user or not verify_password_hash(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Credentials"
            )


class UserService:
    def __init__(self, db=None):
        self.db = db

    def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        payload = validate_jwt_token(token)

        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        user = UserRepository(db).get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if getattr(user, "is_active", True) is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        return user


class EmailService:
    def __init__(self, db):
        self.user_repo = UserRepository(db)
        self.email_repo = EmailRepository(db)

    def create_and_send_email_verification(self, user: User) -> None:
        token = create_email_verification_token()
        hashed_token = self._issue_hashed_token(token)
        self.email_repo.create(
            hashed_token=hashed_token,
            user_id=user.id,
            expires_at=(datetime.now(
                timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTE))
        )

        verification_link = f"{settings.REDIRECT_URL}/verify-email?token={token}"

        send_email_verification_link(verification_link, user.email)

    def validate_email_verification_link(self, token: str) -> json:
        hashed_token = self._issue_hashed_token(token)

        token_record = self.email_repo.is_token_exists(hashed_token)

        if not token_record or token_record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Link"
            )

        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link Expired"
            )

        self.user_repo.update_email_verification_status(token_record.user_id)
        self.email_repo.update_token_record_status(token_record)

        return {"message": "Email Verification Successful"}

    def resend_verification_link(self, user: User, backround_task: BackgroundTasks) -> None:
        if user.is_email_verified:
            return

        now = datetime.now(timezone.utc)

        # Internal helpers

    def _issue_hashed_token(self, token: str) -> str:
        return hash_token(token)
