from prometheus_client import generate_latest
from fastapi import Response, Request
import time

from api_gateway.metrics import Request_Count, Request_Latency

def metrics_middleware_wrapper(app):

    @app.middleware("http")
    async def metrics_gateway_middleware(request: Request, call_next):

        start = time.time()

        response = await call_next(request)

        duration = time.time() - start

        Request_Count.labels(
            method=request.method,
            service="gateway-serivce",
            endpoint=request.url.path
        ).inc()

        Request_Latency.labels(
            method=request.method,
            service="gateway_service",
            endpoint=request.url.path
        ).observe(duration)

        return response
    
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")