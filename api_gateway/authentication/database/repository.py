import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from api_gateway.authentication.database.models import User


class UserRepository:

    """
    Repository layer for user model,
    Handles all database interaction related to users
    """

    def __init__(self, db: Session):
        self.db = db

    # Queries

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        exc = select(User).where(User.email == email)
        return self.db.execute(exc).scalar_one_or_none()

    # Commands

    def create(
            self,
            *,
            email: str,
            hashed_password: str,
            first_name: str,
            last_name: str,
            date_of_birth: date
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def exist_by_email(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email)
        return self.db.execute(stmt).first() is not None

    def update_credentials(
        self,

    )
