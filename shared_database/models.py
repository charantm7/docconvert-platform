import enum

import sqlalchemy
from uuid import uuid4
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Enum, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, CITEXT
from sqlalchemy.sql import func

from shared_database.connection import Base


class AuthProviders(str, enum.Enum):

    LocalAuthentication = "LocalAuthentication"
    Google = "Google"
    GitHub = "GitHub"
    Twitter = "Twitter"

class Role(str, enum.Enum):

    user = "user"
    admin = "admin"


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

class SubscriptionPlan(str, enum.Enum):
    free       = "free"
    pro        = "pro"
    enterprise = "enterprise"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid4, unique=True)

    email = Column(CITEXT, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, nullable=True)

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

    role = Column(Enum(Role), default=Role.user)

    plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.free)

    is_email_verified = Column(
        Boolean,
        server_default=sqlalchemy.false(),
        nullable=True
    )
    email_verified_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    email_verification_sent_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    password_reset_sent_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    password_reseted_at = Column(
        DateTime(timezone=True),
        nullable=True
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

    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default=uuid4
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


class APIKey(TimestampMixin, Base):
    __tablename__ = "api_key"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    hashed_key = Column(String(128), nullable=False, unique=True)

    prefix = Column(String(12), nullable=False, index=True)

    user_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    scopes = Column(ARRAY(String), default=[])
    expiring_at = Column(DateTime(timezone=True), nullable=False)
    
    name = Column(String(100), nullable=True)  

    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship('User', back_populates="api_keys")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                unique=True, nullable=False, default=uuid4)
    hashed_token = Column(String, nullable=False, index=True, unique=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                unique=True, nullable=False, default=uuid4)
    hashed_token = Column(String, nullable=False, index=True, unique=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
