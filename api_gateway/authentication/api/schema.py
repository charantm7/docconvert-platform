from typing import Optional
from zxcvbn import zxcvbn
from pydantic import BaseModel, EmailStr, field_validator, model_validator


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class LoginSchema(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class PasswordResetRequestSchema(BaseModel):
    email: Optional[EmailStr] = None


class PasswordResetSchema(BaseModel):
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, new_password) -> str:
        score = zxcvbn(new_password)["score"]
        if score < 3:
            raise ValueError("Password is too weak")
        return new_password

    @model_validator(mode='after')
    def reset_password_match(self):
        if self.confirm_password is not None and self.new_password != self.confirm_password:
            raise ValueError("Password must match")
        return self


class SignupSchema(LoginSchema, BaseModel):

    confirm_password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, password) -> str:
        score = zxcvbn(password)["score"]
        if score < 3:
            raise ValueError("Password is too weak")
        return password

    @model_validator(mode="after")
    def password_match(self):
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Password does not match")
        return self
