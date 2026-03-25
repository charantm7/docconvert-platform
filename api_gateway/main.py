from redis.asyncio import Redis
from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from common_logging.configuration import setup_logging
from api_gateway.middleware.request_id_middleware import RequestIdMiddleware
from api_gateway.middleware.auth_middleware import DualAuthMiddleware
from api_gateway.settings import settings
from api_gateway.authentication.config.limiter_engine import TokenBucketEngine
from api_gateway.middleware.ratelimiter import RatelimiterMiddleware

from .authentication.api.router import auth
from .routes import (
    upload_proxy,
    download_proxy,
    api_provider_proxy
)
from api_gateway.handlers.exception_handlers import register_exception_handlers

setup_logging(service_name="gateway")


LAU_SCRIPT = """
local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local data = redis.call("HMGET", key, "tokens", "timestamp")

local tokens = tonumber(data[1])
local last_time = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_time = now
end

local delta = math.max(0, now - last_time)
local refill = delta * refill_rate
tokens = math.min(capacity, tokens + refill)

if tokens < 1 then
    return 0
end

tokens = tokens - 1

redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
redis.call("EXPIRE", key, 3600)

return 1
"""


@asynccontextmanager
async def lifespan(app: FastAPI):

    redis = await Redis.from_url(
        settings.REDIS_CONNECTION,
        encoding='utf-8',
        decode_responses=True
    )

    script_sha = await redis.script_load(LAU_SCRIPT)

    limiter = TokenBucketEngine(redis=redis, script=script_sha)

    app.state.limiter = limiter
    app.state.redis = redis

    yield

    await redis.close()

    await upload_proxy._client.aclose()


app = FastAPI(
    title="DocPipe",
    description="A Smart Document Converter from one file type to another!",
    version="1.0.0",
    contact={
        "name": "Charan T M",
        "url": "https://www.linkedin.com/in/charantm/",
        "email": "charanntm.dev@gmail.com"
    },
    lifespan=lifespan
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
app.add_middleware(DualAuthMiddleware)
app.add_middleware(RatelimiterMiddleware,
                   limiter=lambda request: request.app.state.limiter)
register_exception_handlers(app)

app.include_router(upload_proxy.upload)
app.include_router(download_proxy.download)
app.include_router(api_provider_proxy.api_provider)
app.include_router(auth)

Instrumentator().instrument(app).expose(app)


@app.get("/favicon.ico")
def favicon_point():
    return Response(status_code=status.HTTP_200_OK)
