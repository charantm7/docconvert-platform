
from pydantic import BaseModel
from datetime import date



class APICreationSchema(BaseModel):
    name: str
    expire_date: date