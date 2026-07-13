from sqlalchemy.orm import Session

from app.models.category import Category


def get_categories_by_framework(
    db: Session,
    framework_id: int
):
    return (
        db.query(Category)
        .filter(
            Category.framework_id == framework_id
        )
        .all()
    )


def get_category(
    db: Session,
    category_id: int
):
    return (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )


def get_category_by_code(
    db: Session,
    framework_id: int,
    category_code: str
):
    return (
        db.query(Category)
        .filter(
            Category.framework_id == framework_id,
            Category.category_code == category_code
        )
        .first()
    )


def get_or_create_category(
    db: Session,
    framework_id: int,
    category_code: str,
    name: str,
    description: str = None
):
    category = get_category_by_code(
        db,
        framework_id,
        category_code
    )

    if category:
        return category

    category = Category(
        framework_id=framework_id,
        category_code=category_code,
        name=name,
        description=description
    )

    db.add(category)
    db.flush()

    return category
