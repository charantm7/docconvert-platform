
from pydantic import BaseModel
from datetime import date



class APICreationSchema(BaseModel):
    name: str
