from pydantic import BaseModel


class PreSignedSchema(BaseModel):
    filename: str
    content_type: str
