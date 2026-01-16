from fastapi import FastAPI, Response, status

from .routes import (
    upload_proxy
)

app = FastAPI(
    title="DocPipe",
    description="A Smart Document Converter from one file type to another!",
    version="1.0.0",
    contact={
        "name": "Charan T M",
        "url": "https://www.linkedin.com/in/charantm/",
        "email": "charanntm.dev@gmail.com"
    }

)


app.include_router(upload_proxy.upload)


@app.get("/favicon.ico")
def favicon_point():
    return Response(status_code=status.HTTP_200_OK)


