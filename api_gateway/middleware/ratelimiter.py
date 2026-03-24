from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

from api_gateway.settings import settings


def get_identifier(request: Request) -> str:
    user = getattr(request.state, 'user', None)

    if user:
        return f"{user.auth_type}:{user.user_id}"

    return get_remote_address(request)


limiter = Limiter(key_func=get_identifier,
                  storage_uri=settings.REDIS_CONNECTION)


PLAN_CONFIG = {
    "admin": {
        "capacity": 10000,
        "refill_rate": 10000 / 3600
    },
    "free": {
        "capacity": 100,
        "refill_rate": 100 / 3600
    },
    "pro": {
        "capacity": 1000,
        "refill_rate": 1000 / 3600
    },
    "enterprise": {
        "capacity": 5000,
        "refill_rate": 5000 / 3600
    }
}


class RatelimiterMiddleware:

    def __init__(self, app, limiter):
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        limiter = self.limiter(request)

        identifier = get_identifier(request)
        user = getattr(request.state, "user", None)

        if user and user.role == "admin":
            await self.app(scope, receive, send)
            return

        if not user:
            config = {"capacity": 20, "refill_rate": 20/3600}

        else:
            config = PLAN_CONFIG.get(user.plan, PLAN_CONFIG["free"])

        allowed = await limiter.allow(
            key=f"rate:{identifier}",
            capacity=config["capacity"],
            refill_rate=config["refill_rate"]
        )

        if not allowed:
            return JSONResponse(
                status_code=439,
                content={"detail": "Rate limit exceeded"}
            )

        await self.app(scope, receive, send)
