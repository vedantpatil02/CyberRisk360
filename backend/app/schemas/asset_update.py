"""
CyberRisk360

Purpose:
Schema used when updating an existing asset.

Unlike AssetCreate, all fields are optional because users may update
only specific attributes of an asset.
"""

from typing import Optional

from pydantic import BaseModel


class AssetUpdate(BaseModel):

    name: Optional[str] = None

    asset_type: Optional[str] = None

    owner: Optional[str] = None

    criticality: Optional[str] = None

    ip_address: Optional[str] = None

    environment: Optional[str] = None
