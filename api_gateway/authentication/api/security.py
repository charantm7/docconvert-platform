# import
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status


from ...settings import settings


def create_access_token(data: dict) -> str:

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data not found"
        )

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTE)

    to_encode.update({'exp': expire})

    pass
