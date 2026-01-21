from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginSchema(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class SignupSchema(LoginSchema, BaseModel):

    confirm_password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

    @field_validator("confirm_password")
    @classmethod
    def password_match(cls, v, info):
        if v != info.data.get("password"):
            raise ValueError("Password does not match")
        return v
