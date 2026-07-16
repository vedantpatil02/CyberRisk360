"""
CyberRisk360

Purpose:
Tests for the Control Review workflow: submitting a review changes
the control's status and records the event, RBAC (COMPLIANCE_ROLES
submit, READ_ROLES read history), and the 404 path.
"""

from app.models.framework import Framework
from app.models.category import Category
from app.models.control import Control


def _seed_control(db):
    framework = Framework(
        name="Test Framework", short_name="test-fw", version="1.0",
        publisher="Test Publisher"
    )
    db.add(framework)
    db.commit()
    db.refresh(framework)

    category = Category(
        framework_id=framework.id, category_code="TC", name="Test Category"
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    control = Control(
        category_id=category.id, control_id="TC-1", title="Test Control",
        description="d", status="Missing"
    )
    db.add(control)
    db.commit()
    db.refresh(control)

    return control.id


def test_submit_control_review(client, db_session):
    control_id = _seed_control(db_session)

    response = client.post(f"/controls/{control_id}/review", json={
        "new_status": "Implemented", "notes": "Verified MFA is enforced"
    })

    assert response.status_code == 200
    body = response.json()
    assert body["previous_status"] == "Missing"
    assert body["new_status"] == "Implemented"
    assert body["reviewer"] == "test@example.com"
    assert body["notes"] == "Verified MFA is enforced"

    # The control's own status actually changed, not just the review row.
    control_response = client.get(f"/controls/{control_id}")
    assert control_response.json()["status"] == "Implemented"


def test_submit_control_review_not_found(client):
    response = client.post("/controls/999999/review", json={"new_status": "Implemented"})

    assert response.status_code == 404


def test_submit_control_review_requires_compliance_role(client, db_session, as_role):
    control_id = _seed_control(db_session)
    as_role("pentester")

    response = client.post(f"/controls/{control_id}/review", json={"new_status": "Implemented"})

    assert response.status_code == 403


def test_get_control_reviews(client, db_session):
    control_id = _seed_control(db_session)
    client.post(f"/controls/{control_id}/review", json={"new_status": "Partially Implemented"})
    client.post(f"/controls/{control_id}/review", json={"new_status": "Implemented"})

    response = client.get(f"/controls/{control_id}/reviews")

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 2
    assert reviews[0]["new_status"] == "Partially Implemented"
    assert reviews[1]["new_status"] == "Implemented"


def test_get_control_reviews_not_found(client):
    response = client.get("/controls/999999/reviews")

    assert response.status_code == 404


def test_get_control_reviews_read_role_allowed(client, db_session, as_role):
    control_id = _seed_control(db_session)
    as_role("auditor")

    response = client.get(f"/controls/{control_id}/reviews")

    assert response.status_code == 200
