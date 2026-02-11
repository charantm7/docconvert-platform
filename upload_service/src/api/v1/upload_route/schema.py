from pydantic import BaseModel


class PreSignedSchema(BaseModel):
    filename: str
    content_type: str


class ConvertRequest(BaseModel):
    job_id: str
    path: str
    target_format: str
