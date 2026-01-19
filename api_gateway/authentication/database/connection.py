from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from ...settings import settings


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

    finally:
        db.close()
