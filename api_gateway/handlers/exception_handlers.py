# exception_handlers.py

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from exception import UserAlreadyExistsError, AppError, TokenGenerationError, EmailSchedulingError, UserCreationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app):

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
        logger.warning(
            "User already exists",
            extra={
                "stage": "user_exists",
                "path": request.url.path,
            }
        )
        return JSONResponse(status_code=409, content={"detail": exc.message})
    
    @app.exception_handler(TokenGenerationError)
    async def token_generation_handler(request: Request, exc: TokenGenerationError):
        logger.warning(
            "Failed to generate token",
            extra={
                "stage": "token_generation_failed",
                "path": request.url.path,
            }
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.message})
    
    @app.exception_handler(EmailSchedulingError)
    async def email_scheduling_handler(request: Request, exc: EmailSchedulingError):
        logger.warning(
            "Failed to schedule email",
            extra={
                "stage": "email_schedule_failure",
                "path": request.url.path,
            }
        )
        return JSONResponse(status_code=409, content={"detail": exc.message})
    
    @app.exception_handler(UserCreationError)
    async def user_creation_handler(request: Request, exc: UserCreationError):
        logger.warning(
            "User creation failure",
            extra={
                "stage": "user_creation_failure",
                "path": request.url.path,
            }
        )
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.error(
            f"{exc.message}",
            extra={
                "stage": exc.stage,
                "path": request.url.path,
                "error_type": type(exc).__name__,
            }
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "stage":exc.stage},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception",
            extra={
                "stage": "global_unhandled_exception",
                "path": request.url.path,
                "method": request.method,
            }
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )