import functools
import logging
import asyncio

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api_gateway.handlers.exception import AppError

logger = logging.getLogger(__name__)


def log_service_action(stage: str):

    """
    Decorator that logs the exception with stage and re-raise them
    as AppErrors, and keep service method clean
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            
            except AppError:
                raise

            except Exception as e:
                logger.exception(
                    f"Failure at stage: {stage}",
                    extra={"stage": stage, "error": str(e)}
                )
                raise AppError(
                    message=str(e),
                    stage=stage,
                ) from e
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except AppError:
                raise
            except Exception as e:
                logger.exception(
                    f"Failure at stage: {stage}",
                    extra={"stage": stage, "error": str(e)}
                )
                raise AppError(
                    message=str(e),
                    stage=stage,
                ) from e
            
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        
        return sync_wrapper
    
    return decorator
            
            
def handle_db_error(stage: str, message: str):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError:
                raise
            except SQLAlchemyError as e:
                args[0].db.rollback()
                raise AppError(
                    message=message,
                    stage=stage,
                ) from e
            
        return wrapper
    return decorator