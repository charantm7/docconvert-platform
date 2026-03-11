from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request



def get_identifier(request: Request) -> str:
    user = getattr(request.state, 'user', None)

    if user:
        return f"{user.auth_type}:{user.user_id}"

    return get_remote_address(request)


limiter = Limiter(key_func=get_identifier)


FREE_LIMIT      = "100/hour"
PRO_LIMIT       = "1000/hour"
API_KEY_LIMIT   = "500/hour"
STRICT_LIMIT    = "10/minute"



def get_limiter_for_user(request: Request) -> str:

    user = getattr(request.state, "user", None)

    if not user:
        return "50/hour"

    if user.auth_type == "api_key":
        return "500/hour"
    
    