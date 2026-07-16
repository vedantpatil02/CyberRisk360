from sqlalchemy.orm import Session

from app.models.control_review import ControlReview


def list_reviews_for_control(
    db: Session,
    control_id: int
):
    return (
        db.query(ControlReview)
        .filter(ControlReview.control_id == control_id)
        .order_by(ControlReview.reviewed_at)
        .all()
    )


def create_review(
    db: Session,
    **fields
):
    review = ControlReview(**fields)

    db.add(review)
    db.commit()
    db.refresh(review)

    return review
