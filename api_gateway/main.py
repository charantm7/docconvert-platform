from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from common_logging.configuration import setup_logging
from api_gateway.middleware.request_id_middleware import RequestIdMiddleware
from api_gateway.settings import settings

from .authentication.api.router import auth
from .routes import (
    upload_proxy
)

setup_logging(service_name="gateway")


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

app.mount(
    "/static",
    StaticFiles(directory="api_gateway/authentication/static"),
    name='static'
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRETE,
    same_site="lax",
    https_only=False,
)
# app.add_middleware(AuthMiddleware)
app.add_middleware(RequestIdMiddleware)


app.include_router(upload_proxy.upload)
app.include_router(auth)


@app.get("/favicon.ico")
def favicon_point():
    return Response(status_code=status.HTTP_200_OK)
