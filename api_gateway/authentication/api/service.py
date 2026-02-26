import json
import uuid
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, BackgroundTasks, Depends

from api_gateway.authentication.api.security import (
    create_access_token,
    create_refersh_token,
    create_email_verification_token,
    create_password_hash,
    create_password_reset_token,
    hash_token,
    validate_jwt_token,
    verify_password_hash,
    oauth2_scheme
)

from api_gateway.handlers.exception import (
    AppError,
    TokenGenerationError,
    UserAlreadyExistsError,
    UserCreationError,
    EmailSchedulingError
)

from api_gateway.settings import settings
from api_gateway.authentication.config import Oauth2
from api_gateway.handlers.decorators import log_service_action
from api_gateway.authentication.database.connection import get_db
from api_gateway.authentication.database.models import AuthProviders, User
from api_gateway.authentication.config.github_client import GithubOAuthClient
from api_gateway.authentication.config.google_client import GoogleOAuthClient
from api_gateway.authentication.config.twitter_client import TwitterOAuthClient
from api_gateway.authentication.database.repository import EmailRepository, UserRepository
from api_gateway.authentication.api.tasks import send_email_verification_link, send_password_reset_link
from api_gateway.authentication.api.schema import SignupSchema, LoginSchema, PasswordResetSchema, TokenResponse

logger = logging.getLogger(__name__)

VERIFICATION_RESEND_COOLDOWN = timedelta(minutes=5)
PASSWORD_VERIFICATION_RESEND_COOLDOWN = timedelta(minutes=1)


def get_current_user(
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


class TokenService:

    @log_service_action("token_generation")
    @staticmethod
    def generate_tokens(user_id: uuid.UUID,  db) -> dict:
        access_token = create_access_token(str(user_id))
        refresh_token = create_refersh_token(db, user_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }


class AuthService:

    """
    Service layer for Authentication
    Handles all the business logic for local authentication

    Contains:

    1) SignUp
    2) Login
    3) Send Reset Password Link
    4) Reset Password from token

    Error Handled = Done
    Logging = Done
    """

    def __init__(self, db):
        self.db = db
        self.repo = UserRepository(db)
        self.email_service = EmailService(db)

    def signup(self, data: SignupSchema, background_tasks: BackgroundTasks) -> dict:

        logger.info(
            "SignUp attempt",
            extra={
                "stage": "signup_attempt",
                "email": data.email[:3] + "***"
            }
        )
        
        self._ensure_email_not_taken(data.email)
    
        user = self._create_user(
                data,
                primary_provider=AuthProviders.LocalAuthentication,
                last_login_provider=AuthProviders.LocalAuthentication,
                last_login_at=datetime.now(timezone.utc)
            )

        logger.info(
            "User created successfully",
            extra={
                "stage":"user_created_success",
                "user_id": user.id
            }
        )

        access_token, refresh_token = self._issue_token(user)
        
        self._schedule_email_verification(background_tasks, user)
        
        logger.info(
            "Signup successful",
            extra={
                "stage": "signup_success",
                "user_id": user.id
            }
        )
        
        return {'access_token': access_token, "refresh_token": refresh_token}

    def login(self, data: LoginSchema) -> str:

        logger.info(
            "login attempt",
            extra={
                "stage":"login_attempt",
                "email": data.email
            }
        )

        user = self.repo.get_by_email(data.email)
        
        self._ensure_user_availability_and_verify_password(user=user, data=data)
        
        self.repo.update_last_login(
            provider=AuthProviders.LocalAuthentication,
            user=user
        )

        logger.info(
            "Login successful",
            extra={
                "stage":"login_success",
                "user_id": user.id
            }
        )

        access_token, refresh_token = self._issue_token(user)
        
        return {'access_token': access_token, "refresh_token": refresh_token}

    def create_and_send_password_reset_link(self, email: str):

        logger.info(
            "Password reset requested",
            extra={
                "stage":"password_reset_request",
                "email": email[:3] + "****"
            }
        )

        user = self.repo.get_by_email(email)
        if not user:
            logger.warning(
                "password reset requested for not existing user",
                extra={
                    "stage": "password_reset_user_not_found",
                }
            )
            return "If the email exists, a reset link has been sent"

        now = datetime.now(timezone.utc)

        if (
            user.password_reset_sent_at and now -
                user.password_reset_sent_at < PASSWORD_VERIFICATION_RESEND_COOLDOWN
        ):
            logger.warning(
                "Password reset request cooldown failure",
                extra={
                    "stage":"password_reset_request_failure_cooldown_attempt",
                    "user_id": user.id
                }
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another Password reset link",
            )

        token = create_password_reset_token()
        hashed_token = hash_token(token)

        
        self._create_password_reset_record(user, hashed_token)
       
        reset_link = (
            f"{settings.REDIRECT_URL}/reset-password?token={token}"
        )
       
        send_password_reset_link(reset_link, email)
      
        self.repo.update_password_reset_link_sent_at(user)

        logger.info(
            "password reset link sent",
            extra={
                "stage": "password_reset_link_sent",
                "user_id": user.id
            }
        )
        return f"Reset Link sent to {email} successfully"

    @log_service_action("reset_password_from_token")
    def reset_password_from_token(
        self,
        token: str,
        data: PasswordResetSchema
    ):
        logger.info(
            "password reset token validation attempt",
            extra={
                "stage": "password_reset_token_validation"
            }
        )
        hashed_token = hash_token(token)

        token_record = self.repo.is_password_reset_token_exists(hashed_token)

        if not token_record or token_record.used:
            logger.warning(
                "Invalid or used password reset token",
                extra={
                    "stage":"password_reset_invalid_token"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Link"
            )

        if token_record.expires_at < datetime.now(timezone.utc):
            logger.warning(
                "Expired password reset token",
                extra={
                    "stage": "password_reset_token_expired",
                    "user_id": token_record.user_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link Expired"
            )
        user = self.repo.get_by_id(token_record.user_id)
        hashed_new_password = create_password_hash(data.new_password)
        self.repo.update_password(user, hashed_new_password)
        self.repo.update_password_reseted_at(user)
        self.repo.update_password_reset_token_status(token_record)

        logger.info(
            "Password reset successful",
            extra={
                "stage": "password_reset_success",
                "user_id": token_record.user_id
            }
        )
        return "password reset successful"

    # Internal helpers

    def _ensure_email_not_taken(self, email: str) -> None:
        if self.repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

    @log_service_action("signup_email_scheduling_failure")
    def _schedule_email_verification(self, background_tasks, user):
        self.repo.update_email_verification_sent_at(user)
        background_tasks.add_task(
            self.email_service.create_and_send_email_verification,
            user
        )
    
    @log_service_action("user_creation_failure_signup")
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

    @log_service_action("signup_token_generation_failure")
    def _issue_token(self, user: User) -> str:
        refresh_token = create_refersh_token(self.db, user.id)
        access_token = create_access_token(
            subject=str(user.id))
        
        if not refresh_token or access_token:
            raise TokenGenerationError(
                message="Failed to generate token",
                stage="signup_token_generation_failure",
                extra={"user_id": user.id}
            )
        return access_token, refresh_token

    @log_service_action("ensure_user_availability_and_verify_password")
    def _ensure_user_availability_and_verify_password(self, user: User, data: LoginSchema) -> None:
        if not user or not verify_password_hash(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Credentials"
            )
    
    @log_service_action("create_password_reset_record")
    def _create_password_reset_record(self, user: User, hashed_token: str):
        self.repo.create_password_reset_record(
                hashed_token=hashed_token,
                user_id=user.id,
                expires_at=(datetime.now(
                    timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTE))
            )


class OauthService:

    """
    This Service Handles all OAuth authentication

    OAuth SignIn request -> Callback -> Token exchange -> Gets Access Token -> Fetch User

    Error Handling = Done
    Logging = Done
    
    """
    
    def __init__(self, db=None):
        self.user_repo = UserRepository(db)
        self.db = db
        self.google_auth_client = GoogleOAuthClient()
        self.github_auth_client = GithubOAuthClient()
        self.twitter_auth_client = TwitterOAuthClient()

    # login controllers
    async def google_login_service(self, request):
        logger.info(
            "OAuth login redirect initiated",
            extra={"stage": "oauth_google_redirect"}
        )
        return await Oauth2.oauth.google.authorize_redirect(
            request,
            settings.GOOGLE_CALLBACK_REDIRECT_LINK
        )

    async def github_login_service(self, request):
        logger.info(
            "OAuth login redirect initiated",
            extra={"stage": "oauth_github_redirect"}
        )
        return await Oauth2.oauth.github.authorize_redirect(
            request,
            settings.GITHUB_CALLBACK_REDIRECT_LINK
        )

    async def twitter_login_service(self, request):
        logger.info(
            "OAuth login redirect initiated",
            extra={"stage": "oauth_twitter_redirect"}
        )
        return await Oauth2.oauth.twitter.authorize_redirect(
            request,
            settings.X_CALLBACK_REDIRECT_LINK
        )

    # callbacks
    async def google_callback_service(self, request) -> TokenResponse:
        logger.info(
            "OAuth Google callback recieved",
            extra={
                "stage": "oauth_google_callback"
            }
        )
        try:
            token = await Oauth2.oauth.google.authorize_access_token(request)
        except Exception as e:
            logger.warning(
                "OAuth Google exchange token failed",
                extra={
                    "stage": "oauth_google_token_failed",
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        access_token = token.get('access_token')
        userinfo = token.get('userinfo')

        google_user = await self.google_auth_client.fetch_userinfo(access_token)
        self.google_auth_client.validate_user(userinfo['iss'])

        return self._handle_google_user(google_user)

    async def github_callback_service(self, request) -> TokenResponse:
        logger.info(
            "OAuth GitHub callback recieved",
            extra={
                "stage": "oauth_google_callback"
            }
        )
        try:
            token = await Oauth2.oauth.github.authorize_access_token(request)

        except Exception as e:
            logger.warning(
                "OAuth GitHub exchange token failed",
                extra={
                    "stage": "oauth_github_token_failed",
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        user = await self.github_auth_client.fetch_github_userinfo(token)
        print(user)

        return self._handle_github_users(user)

    async def twitter_callback_service(self, request) -> TokenResponse:
        logger.info(
            "OAuth Twitter callback recieved",
            extra={
                "stage": "oauth_twitter_callback"
            }
        )
        try:
            token = await Oauth2.oauth.twitter.authorize_access_token(request)
        except Exception as e:
            logger.warning(
                "OAuth Twitter exchange token failed",
                extra={
                    "stage": "oauth_twitter_token_failed",
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        user = await self.twitter_auth_client.fetch_twitter_userinfo(token)
        return self._handle_twitter_user(user)

    # Internal handlers

    @log_service_action("oauth_handle_google_user")
    def _handle_google_user(self, user_info: dict) -> dict:
        user_id = user_info.get("id")
        email = user_info.get('email')

        if not email or not user_id:
            logger.warning(
                "Invalid Google user payload",
                extra={"stage":"oauth_google_invalid_payload"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google user data"
            )

        user = self.user_repo.get_by_email(email)

        if not user:
            logger.info(
                "Creating new user from google oauth",
                extra={"stage":"oauth_google_user_creation"}
            )
            user = self.user_repo.create(
                email=email,
                first_name=user_info.get('name'),
                is_email_verified=user_info.get('verified_email', False),
                picture=user_info.get('picture'),
                primary_provider=AuthProviders.Google,
                last_login_provider=AuthProviders.Google
            )
        else:
            logger.info(
                "Google OAuth login for existing user",
                extra={
                    "stage": "oauth_google_existing_user",
                    "user_id": user.id
                }
            )
            self.user_repo.update_last_login(
                provider=AuthProviders.Google, user=user)

        logger.info(
            "OAuth Google login successful",
            extra={
                "stage": "oauth_google_success",
                "user_id": user.id
            }
        )
        return TokenService.generate_tokens(user_id=user.id, db=self.db)

    @log_service_action("handle_github_users")
    def _handle_github_users(self, user_info: dict):
        email = user_info['email']

        if not email:
            logger.warning(
                "Invalid github user payload",
                extra={"stage":"oauth_github_invalid_payload"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub user data"
            )

        user = self.user_repo.get_by_email(email)

        if not user:
            logger.info(
                "Creating new user from Github oauth",
                extra={"stage":"oauth_github_user_creation"}
            )
            user = self.user_repo.create(
                email=email,
                first_name=user_info.get('name'),
                is_email_verified=True,
                picture=user_info.get('avatar_url'),
                primary_provider=AuthProviders.GitHub,
                last_login_provider=AuthProviders.GitHub,
            )
        else:
            logger.info(
                "GitHub OAuth login for existing user",
                extra={
                    "stage": "oauth_github_existing_user",
                    "user_id": user.id
                }
            )
            self.user_repo.update_last_login(
                provider=AuthProviders.GitHub, user=user)
            
        logger.info(
            "OAuth GitHub login successful",
            extra={
                "stage": "oauth_github_success",
                "user_id": user.id
            }
        )
        return TokenService.generate_tokens(user_id=user.id, db=self.db)

    @log_service_action("handle_twitter_user")
    def _handle_twitter_user(self, user_info: dict) -> dict:
        username = user_info['data']['username']

        if not username:
            logger.warning(
                "Invalid twitter user payload",
                extra={"stage":"oauth_twitter_invalid_payload"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid twitter user data"
            )

        user = self.user_repo.get_by_username(username)

        if not user:
            logger.info(
                "Creating new user from twitter oauth",
                extra={"stage":"oauth_twitter_user_creation"}
            )
            user = self.user_repo.create(
                username=username,
                first_name=user_info['data']['name'],
                is_email_verified=True,
                picture=user_info['data']['profile_image_url'],
                primary_provider=AuthProviders.Twitter,
                last_login_provider=AuthProviders.Twitter
            )
        else:
            logger.info(
                "Twitter OAuth login for existing user",
                extra={
                    "stage": "oauth_twitter_existing_user",
                    "user_id": user.id
                }
            )
            self.user_repo.update_last_login(
                provider=AuthProviders.Twitter, user=user)
            
        logger.info(
            "OAuth twitter login successful",
            extra={
                "stage": "oauth_twitter_success",
                "user_id": user.id
            }
        )
        return TokenService.generate_tokens(user_id=user.id, db=self.db)


class EmailService:

    """
    Email service layer
    This service handles all the business logic for email verification

    Contains:

    1) Send email verification Link
    2) Validate email verification link
    3) Resend email verification link
    
    """
    
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
        self.user_repo.update_email_verified_at(token_record.user_id)
        self.email_repo.update_token_record_status(token_record)

        return {"message": "Email Verification Successful"}

    def resend_verification_link(self, user: User, backround_task: BackgroundTasks) -> str:
        if user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )

        now = datetime.now(timezone.utc)

        if (
            user.email_verification_sent_at and now -
                user.email_verification_sent_at < VERIFICATION_RESEND_COOLDOWN
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification email",
            )

        backround_task.add_task(
            self.create_and_send_email_verification,
            user
        )

        self.user_repo.update_email_verification_sent_at(user)

        return {"message":"Email sent successfully"}

        # Internal helpers
    def _issue_hashed_token(self, token: str) -> str:
        return hash_token(token)
