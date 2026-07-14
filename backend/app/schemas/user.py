from typing import Optional
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "analyst"


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8)