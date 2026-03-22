from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

from api_gateway.settings import settings



def get_identifier(request: Request) -> str:
    user = getattr(request.state, 'user', None)

    if user:
        return f"{user.auth_type}:{user.user_id}"

    return get_remote_address(request)


limiter = Limiter(key_func=get_identifier, storage_uri=settings.REDIS_CONNECTION)


ROLE_LIMITS = {
    "admin": "10000/hour",          
}

PLAN_LIMITS = {
    "free"       : "100/hour",
    "pro"        : "1000/hour",
    "enterprise" : "5000/hour",
}

UNAUTHENTICATED_LIMIT = "20/hour" 


def get_limiter_for_user(request: Request) -> str:

    user = getattr(request.state, "user", None)

    if not user:
        return UNAUTHENTICATED_LIMIT
    
    if getattr(user, "role", None) in ROLE_LIMITS:
        return ROLE_LIMITS[user.role]

    return PLAN_LIMITS.get(getattr(user, "plan", None), PLAN_LIMITS["free"])
        

def dynamic_limit(request: Request):
    return get_limiter_for_user(request)