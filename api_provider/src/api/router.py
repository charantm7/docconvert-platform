from fastapi import APIRouter


provider = APIRouter()

@provider.post("/create-api")
async def create_new_api():
    return