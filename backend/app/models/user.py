"""
CyberRisk360

Purpose:
Database model representing platform users.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from pydantic import BaseModel, EmailStr

from app.database import Base


class User(Base):
    """
    User table.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=False
    )

    role = Column(
        String,
        default="analyst"
    )



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str