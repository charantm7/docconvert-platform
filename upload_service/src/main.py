from fastapi import FastAPI

from upload_service.src.api.routers import upload_service_router

app = FastAPI()

app.include_router(upload_service_router)


@app.get("/upload/file")
def upload():
    return {"message": "hi this is upload router"}
