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


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str
):
    user = User(
        username=username,
        email=email,
        password=password,
        role=role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
