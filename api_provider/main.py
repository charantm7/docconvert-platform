from fastapi import FastAPI, Response, status

from common_logging.configuration import setup_logging
from api_provider.src.api.router import provider

app = FastAPI(
    title="API Provider Service",
    description="This service provides the apikey service which use to access all the routes"
)

app.include_router(provider)
setup_logging(service_name="api-provider")

@app.get("/health")
async def health_check():
    return "API Provider Service is Up"

@app.get("/favicon.ico")
def favicon_point():
    return Response(status_code=status.HTTP_200_OK)