from sqlalchemy.orm import Session

from app.models.cisa_kev_entry import CisaKevEntry


def get_by_cve(
    db: Session,
    cve_id: str
):
    return (
        db.query(CisaKevEntry)
        .filter(CisaKevEntry.cve_id == cve_id)
        .first()
    )


def get_latest_fetch_time(
    db: Session
):
    """
    The most recent fetched_at across the whole catalog, or None if
    it's never been populated. Every row from one catalog pull shares
    the same fetched_at, so the max is just that pull's timestamp.
    """

    entry = (
        db.query(CisaKevEntry)
        .order_by(CisaKevEntry.fetched_at.desc())
        .first()
    )

    return entry.fetched_at if entry else None


def replace_catalog(
    db: Session,
    entries: list,
    fetched_at
):
    """
    Replace the entire cached catalog in one transaction - a full
    replace rather than a diff/upsert, so a CVE CISA removes from the
    catalog over time is correctly dropped here too, not just ones
    that get added.
    """

    db.query(CisaKevEntry).delete()

    for entry in entries:
        db.add(
            CisaKevEntry(
                cve_id=entry["cve_id"],
                vulnerability_name=entry.get("vulnerability_name"),
                date_added=entry.get("date_added"),
                due_date=entry.get("due_date"),
                required_action=entry.get("required_action"),
                known_ransomware_use=entry.get("known_ransomware_use"),
                notes=entry.get("notes"),
                fetched_at=fetched_at,
            )
        )

    db.commit()
