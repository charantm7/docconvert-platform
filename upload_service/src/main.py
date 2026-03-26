from fastapi import FastAPI
from contextlib import asynccontextmanager

from upload_service.src.api.routers import upload_service_router
from upload_service.src.queue.producer import init_rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_rabbitmq()

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(upload_service_router)


@app.get("/upload/file")
def upload():
    return {"message": "hi this is upload router"}
