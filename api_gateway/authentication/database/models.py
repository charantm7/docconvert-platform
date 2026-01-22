import enum

import sqlalchemy
from uuid import uuid4
from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, CITEXT
from sqlalchemy.sql import func

from api_gateway.authentication.database.connection import Base


class AuthProviders(str, enum.Enum):

    LocalAuthentication = "LocalAuthentication"
    Google = "Google"
    GitHub = "GitHub"
    Twitter = "Twitter"


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid4, unique=True)

    email = Column(CITEXT, unique=True, index=True, nullable=False)

    hashed_password = Column(
        String(255),
        nullable=True,
        comment="bcrypt hash"
    )

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=True)

    about = Column(String(50), nullable=True)
    picture = Column(String, nullable=True)

    date_of_birth = Column(Date, nullable=True)

    is_verified = Column(
        Boolean,
        server_default=sqlalchemy.false(),
        nullable=False
    )

    primary_provider = Column(
        Enum(AuthProviders,
             name="auth_providers"
             ),
        nullable=False
    )

    last_login_provider = Column(
        Enum(AuthProviders, name="auth_providers"),
        nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=sqlalchemy.true()
    )


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False
    )
    hashed_refresh_token = Column(String, nullable=False)
    expire_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    is_revoked = Column(Boolean, default=False)

    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete='CASCADE')
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                unique=True, nullable=False)
    hashed_token = Column(String, nullable=False, index=True, unique=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
