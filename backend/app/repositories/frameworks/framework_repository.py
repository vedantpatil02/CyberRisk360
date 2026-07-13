from sqlalchemy.orm import Session

from app.models.framework import Framework


def get_all_frameworks(
    db: Session
):
    return (
        db.query(Framework)
        .all()
    )


def get_framework(
    db: Session,
    framework_id: int
):
    return (
        db.query(Framework)
        .filter(
            Framework.id == framework_id
        )
        .first()
    )


def get_framework_by_short_name(
    db: Session,
    short_name: str
):
    return (
        db.query(Framework)
        .filter(
            Framework.short_name == short_name
        )
        .first()
    )


def get_or_create_framework(
    db: Session,
    metadata: dict
):
    framework = get_framework_by_short_name(
        db,
        metadata["short_name"]
    )

    if framework:
        return framework

    framework = Framework(
        name=metadata["name"],
        short_name=metadata["short_name"],
        version=metadata["version"],
        publisher=metadata["publisher"],
        description=metadata.get("description"),
        release_year=metadata.get("release_year")
    )

    db.add(framework)
    db.flush()

    return framework


def create_framework(
    db: Session,
    **fields
):
    framework = Framework(**fields)

    db.add(framework)
    db.commit()
    db.refresh(framework)

    return framework


def update_framework(
    db: Session,
    framework: Framework,
    updates: dict
):
    for field, value in updates.items():
        setattr(framework, field, value)

    db.commit()
    db.refresh(framework)

    return framework


def delete_framework(
    db: Session,
    framework: Framework
):
    db.delete(framework)
    db.commit()
