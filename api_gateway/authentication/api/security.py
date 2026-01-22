import hashlib
import secrets
import uuid
import jwt
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from jinja2 import FileSystemLoader, select_autoescape, Environment

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api_gateway.authentication.database.repository import UserRepository
from api_gateway.settings import settings
from api_gateway.authentication.database.models import RefreshToken


hashing_context = CryptContext(
    schemes=["bcrypt"],
    deprecated='auto',
    bcrypt__ident="2b"
)

env = Environment(
    loader=FileSystemLoader("api_gateway/authentication/templates"),
    autoescape=select_autoescape(["html", "xml"])
)


def render_email_template(template_name: str, context: dict):
    template = env.get_template(template_name)
    return template.render(context)


def create_password_hash(data: str):
    return hashing_context.hash(data)


def verify_password_hash(password: str, hashed: str):
    try:
        return hashing_context.verify(password, hashed)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


def hash_token(data: str):
    return hashlib.sha256(data.encode()).hexdigest()


def create_access_token(
        subject: str,
        expire_delta: timedelta | None = None
) -> str:

    expire = datetime.now(timezone.utc) + (
        expire_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTE)
    )

    payload = {
        "sub": subject,
        "expire": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access"
    }

    return jwt.encode(
        payload=payload,
        key=settings.JWT_SECRETE,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refersh_token(db: Session, user_id):

    refresh_token = secrets.token_urlsafe(32)

    hashed_refersh_token = hash_token(data=refresh_token)

    refresh_db = RefreshToken(
        user_id=user_id,
        hashed_refersh_token=hashed_refersh_token,
        expire_at=datetime.now(timezone.utc) + timedelta(days=7)
    )

    db.add(refresh_db)
    db.commit()

    return refresh_token


def create_email_verification_token() -> str:
    return secrets.token_urlsafe(32)


def validate_jwt_token(token: str, db: Session):

    payload = jwt.decode(
        token,
        settings.JWT_SECRETE,
        algorithms=['HS256']
    )

    if payload.get("type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    user = UserRepository(db).get_by_id(payload['sub'])

    if not user:
        HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}
