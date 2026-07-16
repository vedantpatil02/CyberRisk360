from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "analyst"
    # Organization to join, by slug. Defaults to the "default" org when
    # omitted. (In production, open self-registration should be replaced
    # by org-scoped invitations; this keeps dev onboarding simple.)
    org_slug: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8)


class UserRoleUpdate(BaseModel):
    role: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    org_id: int
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None