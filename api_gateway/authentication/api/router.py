from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api_gateway.authentication.database.connection import get_db
from api_gateway.authentication.database.models import User, AuthProviders
from api_gateway.authentication.database.repository import UserRepository
from api_gateway.authentication.api.schema import SignupSchema, LoginSchema, TokenResponse
from api_gateway.authentication.api.security import verify_hash, create_access_token, create_hash

auth = APIRouter()


@auth.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED
)
async def login(
    data: LoginSchema,
    db: Session = Depends(get_db)
):
    repo = UserRepository(db=db)

    user = repo.get_by_email(data.email)

    if not user or not verify_hash(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")

    access_token = create_access_token(subject=str(user.id))

    return {'access_token': access_token}


@auth.post(
    '/signup',
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED
)
async def signup(
    data: SignupSchema,
    db: Session = Depends(get_db)
):
    repo = UserRepository(db=db)

    if repo.exist_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exits"
        )

    user = repo.create(
        email=data.email,
        hashed_password=create_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth
    )

    access_token = create_access_token(subject=str(user.id))

    return {'access_token': access_token}
