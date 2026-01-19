from datetime import date

from typing import Optional
from pydantic import BaseModel, EmailStr


class SignupSchema(BaseModel):

    email: Optional[EmailStr] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
