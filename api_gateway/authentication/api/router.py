import httpx
from fastapi import APIRouter, Depends, Request, status, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from api_gateway.authentication.api import security
from api_gateway.authentication.api.service import AuthService, EmailService, get_current_user
from api_gateway.authentication.config import Oauth2
from api_gateway.authentication.database.connection import get_db
from api_gateway.authentication.database.models import User, AuthProviders
from api_gateway.authentication.database.repository import UserRepository
from api_gateway.authentication.api.schema import SignupSchema, LoginSchema, TokenResponse, PasswordResetRequestSchema, PasswordResetSchema

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
    return AuthService(db).login(data)


@auth.post(
    '/signup',
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED
)
async def signup(
    data: SignupSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    return AuthService(db).signup(
        data=data,
        background_tasks=background_tasks
    )


@auth.post(
    "/verify-email"
)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    return EmailService(db).validate_email_verification_link(token)


@auth.post(
    "/resend-email-verification"
)
async def resend_email_verification(
    background_task: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return EmailService(db).resend_verification_link(
        user=current_user,
        backround_task=background_task
    )


@auth.post("/reset-password-request")
async def reset_password_request(
    data: PasswordResetRequestSchema,
    db: Session = Depends(get_db)
):
    return AuthService(db).create_and_send_password_reset_link(data.email)


@auth.post('/reset-password')
async def reset_password(
    token: str,
    data: PasswordResetSchema,
    db: Session = Depends(get_db)
):
    return AuthService(db).reset_password_from_token(token, data)


@auth.get('/google/login')
async def google_login(request: Request):
    redirect_url = 'http://127.0.0.1:8000/google/callback'
    return await Oauth2.oauth.google.authorize_redirect(request, redirect_url)


@auth.get('/google/callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    try:

        token = await Oauth2.oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    access_token = token.get('access_token')
    userinfo = token.get('userinfo')
    iss = userinfo['iss']

    async with httpx.AsyncClient() as client:

        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    user_info = response.json()
    email = user_info['email']
    name = user_info['name']
    user_id = user_info['id']
    is_verified = user_info['verified_email']
    picture = user_info['picture']

    if iss not in ["https://accounts.google.com", "accounts.google.com"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Google authentication failed.")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Google authentication failed.")

    user = repo.get_by_email(email)
    if not user:
        user = repo.create(
            email=email,
            first_name=name,
            is_email_verified=is_verified,
            picture=picture,
            primary_provider=AuthProviders.Google,
            last_login_provider=AuthProviders.Google
        )

    access_token = security.create_access_token(subject=str(user.id))
    refresh_token = security.create_refersh_token(db, user.id)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'Bearer'}


@auth.get('/github/login')
async def github_login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/github/callback"
    return await Oauth2.oauth.github.authorize_redirect(request, redirect_uri)


@auth.get('/github/callback')
async def github_callback(request: Request, db: Session = Depends(get_db)):
    repo = UserRepository(db)

    token = await Oauth2.oauth.github.authorize_access_token(request)
    user_data = await Oauth2.oauth.github.get('user', token=token)

    email_data = await Oauth2.oauth.github.get('user/emails', token=token)
    emails = email_data.json()
    user = user_data.json()

    verified_email = [
        item['email']
        for item in emails
        if item.get('primary') is True
    ]
    picture = user['avatar_url']
    about = user['bio']
    first_name = user['name']

    user = repo.get_by_email(verified_email[0])
    if not user:
        user = repo.create(
            email=verified_email[0],
            first_name=first_name,
            is_email_verified=True,
            picture=picture,
            primary_provider=AuthProviders.GitHub,
            last_login_provider=AuthProviders.GitHub,
            about=about
        )

    access_token = security.create_access_token(subject=str(user.id))
    refresh_token = security.create_refersh_token(db, user.id)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'Bearer'}


@auth.get("/twitter/login")
async def twitter_login(request: Request):
    return await Oauth2.oauth.twitter.authorize_redirect(
        request,
        "http://docconvert.local:8000/twitter/callback",
    )


@auth.get("/twitter/callback")
async def twitter_callback(request: Request, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    try:
        token = await Oauth2.oauth.twitter.authorize_access_token(request)
        user = await Oauth2.oauth.twitter.get(
            "https://api.x.com/2/users/me",
            token=token,
            params={"user.fields": "id,name,username,profile_image_url"}
        )
        user_info = user.json()
        username = user_info['data']['username']
        picture = user_info['data']['profile_image_url']
        first_name = user_info['data']['name']

        user = repo.get_by_username(username)
        if not user:
            user = repo.create(
                first_name=first_name,
                is_email_verified=True,
                picture=picture,
                primary_provider=AuthProviders.Twitter,
                last_login_provider=AuthProviders.Twitter,
                username=username
            )

        access_token = security.create_access_token(subject=str(user.id))
        refresh_token = security.create_refersh_token(db, user.id)

        return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'Bearer'}
    except Exception as e:
        return str(e)
