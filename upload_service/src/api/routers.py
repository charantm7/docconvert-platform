from fastapi import APIRouter
from upload_service.src.api.v1.upload_route.router import upload_service


upload_service_router = APIRouter()

upload_service_router.include_router(upload_service)


__all__ = ['upload_service_router']