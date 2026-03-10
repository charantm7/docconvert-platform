
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ScopeEnum(str, Enum):

    document_upload  = "document:upload"
    document_read  = "document:read"
    document_delete  = "document:delete"

    convert_create = "convert:create"
    convert_read = "convert:read"
    convert_download = "convert:download"
    convert_cancel = "convert:cancel"

    api_read = "api:read"      
    api_write = "api:write"



class APICreationSchema(BaseModel):
    name: str
    scopes: list[ScopeEnum]
    expire_at: datetime | None = None



class APITokenResponseSchema(BaseModel):
    id: str
    name: str
    scopes: list[str]
    token: str
    expire_at: datetime | None
