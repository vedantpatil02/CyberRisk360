from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(
    db: Session,
    email: str
):
    return (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )


def get_by_id(
    db: Session,
    user_id: int
):
    return (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )


def get_by_id_in_org(
    db: Session,
    user_id: int,
    org_id: int = None
):
    """
    Org-scoped user lookup. `org_id=None` = no restriction (super-admin).
    Used to validate an assignee_id belongs to the caller's org before
    it's attached to a vulnerability/risk.
    """

    query = db.query(User).filter(User.id == user_id)

    if org_id is not None:
        query = query.filter(User.org_id == org_id)

    return query.first()


def list_users(
    db: Session,
    org_id: int = None
):
    """
    List users. `org_id=None` = no restriction (super-admin sees every
    org), mirroring `get_by_id_in_org`'s convention.
    """

    query = db.query(User)

    if org_id is not None:
        query = query.filter(User.org_id == org_id)

    return query.order_by(User.id).all()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str,
    org_id: int
):
    user = User(
        username=username,
        email=email,
        password=password,
        role=role,
        org_id=org_id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
