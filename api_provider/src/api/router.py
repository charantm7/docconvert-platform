from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from api_provider.src.api.service import APIService
from api_provider.src.api.schema import APICreationSchema
from shared_database.connection import get_db

provider = APIRouter()

@provider.post("/create-api")
async def create_new_api(data: APICreationSchema ,request: Request, db:Session = Depends(get_db)):
    return APIService(request.headers.get('User-Id'), db).create_new_token(data)