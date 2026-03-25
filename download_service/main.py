from fastapi import FastAPI

from download_service.api.download_route import downloader

app = FastAPI()

app.include_router(downloader)


@app.get("/download/health")
def download():
    return {"message": "hi this is download route"}
