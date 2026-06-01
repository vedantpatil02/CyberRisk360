from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base


class Asset(Base):

    __tablename__ = "assets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    asset_type = Column(
        String,
        nullable=False
    )

    owner = Column(
        String,
        nullable=False
    )

    criticality = Column(
        String,
        nullable=False
    )

    ip_address = Column(
        String,
        nullable=True
    )

    environment = Column(
        String,
        nullable=False
    )