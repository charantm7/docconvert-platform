import enum

import sqlalchemy
from uuid import uuid4
from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, CITEXT
from sqlalchemy.sql import func
from api_provider.src.database.connection import Base


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


class APIKey(TimestampMixin, Base):
    __tablename__ = "api_key"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    hashed_key = Column(String(128), nullable=False, unique=True)

    prefix = Column(String(12), nullable=False, index=True)

    user_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    expiring_at = Column(DateTime(timezone=True), nullable=False)
    
    name = Column(String(100), nullable=True)  

    is_active = Column(Boolean, default=True, nullable=False)