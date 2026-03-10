
from pydantic import BaseModel
from datetime import date



class APICreationSchema(BaseModel):
    name: str


class APITokenResponseSchema(BaseModel):
    token_type: str = "Bearer"
    token: str
