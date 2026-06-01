from pydantic import BaseModel


class AssetCreate(BaseModel):

    name: str

    asset_type: str

    owner: str

    criticality: str

    ip_address: str | None = None

    environment: str