import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from api_gateway.handlers.exception import AppError

from api_gateway.settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.POSTGRES_URL,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 5
    }
)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database session error occurred",
            extra={"stage":"database_session_error"}
        )
        raise
    except AppError:
        raise 
    
    except Exception:
        db.rollback()
        logger.exception(
            "Unexpected error during DB session",
            extra={"stage":"db_unexpected_error"}
        )
        raise

    finally:
        try:
            db.close()
        except Exception:
            logger.exception(
                "Failed to close database session",
                extra={"stage": "db_close_failure"}
            )
