from app.repositories.assets.asset_repository import (
    get_asset_by_ip,
    create_asset
)


def get_or_create_asset(
    db,
    ip_address,
    org_id
):
    """
    Find (or create) the asset for an IP within one organization. The
    same IP in two different orgs is two distinct assets.
    """

    asset = get_asset_by_ip(db, ip_address, org_id=org_id)

    if asset:
        return asset

    return create_asset(
        db,
        name=f"Host-{ip_address}",
        asset_type="Server",
        owner="Imported",
        criticality="Medium",
        ip_address=ip_address,
        environment="Unknown",
        org_id=org_id
    )
