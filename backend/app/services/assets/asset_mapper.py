from app.repositories.assets.asset_repository import (
    get_asset_by_ip,
    create_asset
)


def get_or_create_asset(
    db,
    ip_address
):

    asset = get_asset_by_ip(db, ip_address)

    if asset:
        return asset

    return create_asset(
        db,
        name=f"Host-{ip_address}",
        asset_type="Server",
        owner="Imported",
        criticality="Medium",
        ip_address=ip_address,
        environment="Unknown"
    )
