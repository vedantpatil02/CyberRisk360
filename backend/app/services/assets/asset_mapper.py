from app.models.asset import Asset


def get_or_create_asset(
    db,
    ip_address
):

    asset = (
        db.query(Asset)
        .filter(
            Asset.ip_address == ip_address
        )
        .first()
    )

    if asset:
        return asset

    asset = Asset(
        name=f"Host-{ip_address}",
        asset_type="Server",
        owner="Imported",
        criticality="Medium",
        ip_address=ip_address,
        environment="Unknown"
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset