"""
CyberRisk360

Purpose:
Tests for framework management endpoints (create, list, get,
update, delete), the generic frameworks/ directory scanner, the
generic category-deriving importer, and bootstrap-import
visibility through the API.
"""

from app.core.constants import FRAMEWORKS_DIR
from app.services.frameworks.framework_loader import (
    load_framework,
    discover_frameworks
)
from app.services.frameworks.framework_importer import import_framework
from app.repositories.frameworks.framework_repository import (
    get_framework_by_short_name
)
from app.repositories.categories.category_repository import (
    get_categories_by_framework
)

EXPECTED_FRAMEWORKS = {
    "nist-csf",
    "iso27001",
    "cis",
    "owasp-asvs",
    "owasp-top10"
}


def _framework_payload(short_name="test-fw"):
    return {
        "name": "Test Framework",
        "short_name": short_name,
        "version": "1.0",
        "publisher": "Test Publisher",
        "description": "A framework used in tests.",
        "release_year": 2026
    }


def test_create_framework(client):
    response = client.post("/frameworks", json=_framework_payload("create-fw"))

    assert response.status_code == 200

    data = response.json()

    assert data["short_name"] == "create-fw"
    assert data["id"] is not None


def test_create_framework_duplicate_short_name_conflicts(client):
    client.post("/frameworks", json=_framework_payload("dup-fw"))
    response = client.post("/frameworks", json=_framework_payload("dup-fw"))

    assert response.status_code == 409


def test_list_frameworks(client):
    client.post("/frameworks", json=_framework_payload("list-fw"))

    response = client.get("/frameworks")

    assert response.status_code == 200

    short_names = [framework["short_name"] for framework in response.json()]

    assert "list-fw" in short_names


def test_get_framework(client):
    created = client.post(
        "/frameworks", json=_framework_payload("get-fw")
    ).json()

    response = client.get(f"/frameworks/{created['id']}")

    assert response.status_code == 200
    assert response.json()["short_name"] == "get-fw"


def test_get_framework_not_found(client):
    response = client.get("/frameworks/999999")

    assert response.status_code == 404


def test_update_framework(client):
    created = client.post(
        "/frameworks", json=_framework_payload("update-fw")
    ).json()

    response = client.patch(
        f"/frameworks/{created['id']}",
        json={"description": "Updated description"}
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_update_framework_not_found(client):
    response = client.patch(
        "/frameworks/999999",
        json={"description": "does not matter"}
    )

    assert response.status_code == 404


def test_delete_framework(client):
    created = client.post(
        "/frameworks", json=_framework_payload("delete-fw")
    ).json()

    response = client.delete(f"/frameworks/{created['id']}")
    assert response.status_code == 200

    follow_up = client.get(f"/frameworks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_framework_not_found(client):
    response = client.delete("/frameworks/999999")

    assert response.status_code == 404


def test_discover_frameworks_finds_all_five():
    """
    The generic scanner must find every framework/version under
    frameworks/ without any framework name hardcoded anywhere.
    """

    discovered = discover_frameworks(FRAMEWORKS_DIR)

    assert EXPECTED_FRAMEWORKS <= set(discovered.keys())

    for short_name in EXPECTED_FRAMEWORKS:
        metadata = load_framework(discovered[short_name]["metadata_path"])
        assert metadata["short_name"] == short_name


def test_import_framework_derives_multiple_categories_generically(db_session):
    """
    The importer must not collapse every control into a single
    catch-all category — it should derive distinct category codes
    from control_id structure (e.g. NIST's "PR.AC-1"/"PR.AC-3" share
    a "PR.AC" category, but different prefixes get different ones).
    """

    discovered = discover_frameworks(FRAMEWORKS_DIR)

    controls = load_framework(discovered["nist-csf"]["framework_path"])
    metadata = load_framework(discovered["nist-csf"]["metadata_path"])

    import_framework(metadata, controls, db_session)

    framework = get_framework_by_short_name(db_session, "nist-csf")
    categories = get_categories_by_framework(db_session, framework.id)
    category_codes = {category.category_code for category in categories}

    assert len(categories) > 1
    assert "GENERAL" not in category_codes
    assert {"PR.AC", "ID.AM"} <= category_codes


def test_bootstrap_imported_frameworks_are_exposed_via_api(client, db_session):
    """
    Every framework imported the same way bootstrap_database.py
    imports them (framework_importer.import_framework, driven by
    discover_frameworks) must be visible through the management API,
    not just the import pipeline.
    """

    discovered = discover_frameworks(FRAMEWORKS_DIR)

    assert EXPECTED_FRAMEWORKS <= set(discovered.keys())

    for short_name, paths in discovered.items():
        controls = load_framework(paths["framework_path"])
        metadata = load_framework(paths["metadata_path"])

        import_framework(metadata, controls, db_session)

    list_response = client.get("/frameworks")
    short_names = {framework["short_name"] for framework in list_response.json()}

    assert EXPECTED_FRAMEWORKS <= short_names

    for framework in list_response.json():
        detail_response = client.get(f"/frameworks/{framework['id']}")
        assert detail_response.status_code == 200
        assert detail_response.json()["short_name"] == framework["short_name"]
