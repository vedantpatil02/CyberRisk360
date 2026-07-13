"""
CyberRisk360

Purpose:
Business logic for compliance framework management (CRUD).
"""

from app.repositories.frameworks.framework_repository import (
    get_all_frameworks,
    get_framework,
    get_framework_by_short_name,
    create_framework as db_create_framework,
    update_framework as db_update_framework,
    delete_framework as db_delete_framework
)


def list_frameworks(db):
    """
    Return all frameworks.
    """

    return get_all_frameworks(db)


def get_framework_detail(db, framework_id):
    """
    Return a single framework, or None if it doesn't exist.
    """

    return get_framework(db, framework_id)


def create_framework(db, framework):
    """
    Create a framework. Returns None if a framework with the
    same short_name already exists.
    """

    if get_framework_by_short_name(db, framework.short_name):
        return None

    return db_create_framework(
        db,
        name=framework.name,
        short_name=framework.short_name,
        version=framework.version,
        publisher=framework.publisher,
        description=framework.description,
        release_year=framework.release_year
    )


def update_framework(db, framework_id, updates: dict):
    """
    Apply partial updates to a framework. Returns None if
    the framework doesn't exist.
    """

    framework = get_framework(db, framework_id)

    if not framework:
        return None

    return db_update_framework(db, framework, updates)


def delete_framework(db, framework_id):
    """
    Delete a framework. Returns False if it doesn't exist.
    """

    framework = get_framework(db, framework_id)

    if not framework:
        return False

    db_delete_framework(db, framework)

    return True
