"""
CyberRisk360

Cross-organization isolation tests - the core guarantee of Phase 4:
a user in one organization can never read or reach another's data, while
a platform super-admin spans all organizations.
"""

from app.models.organization import Organization
from app.repositories.assets.asset_repository import create_asset
from app.repositories.vulnerabilities.vulnerability_repository import (
    create_vulnerability,
)
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN

ORG1 = 1
ORG2 = 2


def _make_org2(db):
    db.add(Organization(id=ORG2, name="Second Org", slug="second"))
    db.commit()


def _asset(db, org_id, ip):
    return create_asset(
        db,
        name=f"Host-{ip}",
        asset_type="server",
        owner="Team",
        criticality="High",
        ip_address=ip,
        environment="prod",
        org_id=org_id,
    )


def _vuln(db, org_id, asset_id):
    create_vulnerability(
        db,
        title="Finding",
        plugin_id=None,
        cve_id=None,
        solution=None,
        ip_address="10.0.0.1",
        description="d",
        asset_id=asset_id,
        cvss_score=9.0,
        severity="Critical",
        owner="x",
        status="Open",
        org_id=org_id,
    )
    db.commit()


def _seed_two_orgs(db):
    _make_org2(db)
    a1 = _asset(db, ORG1, "10.0.0.1")
    a2 = _asset(db, ORG2, "10.0.0.2")
    _vuln(db, ORG1, a1.id)
    _vuln(db, ORG2, a2.id)
    return a1, a2


# --- read isolation ----------------------------------------------------

def test_assets_are_isolated_by_org(client, db_session, as_user):
    _seed_two_orgs(db_session)

    as_user(role=ROLE_ADMIN, org_id=ORG1)
    org1_assets = client.get("/assets").json()
    assert len(org1_assets) == 1
    assert org1_assets[0]["org_id"] == ORG1

    as_user(role=ROLE_ADMIN, org_id=ORG2)
    org2_assets = client.get("/assets").json()
    assert len(org2_assets) == 1
    assert org2_assets[0]["org_id"] == ORG2


def test_vulnerabilities_are_isolated_by_org(client, db_session, as_user):
    _seed_two_orgs(db_session)

    as_user(role=ROLE_ADMIN, org_id=ORG1)
    v1 = client.get("/vulnerabilities").json()
    assert len(v1) == 1
    assert all(v["org_id"] == ORG1 for v in v1)

    as_user(role=ROLE_ADMIN, org_id=ORG2)
    v2 = client.get("/vulnerabilities").json()
    assert len(v2) == 1
    assert all(v["org_id"] == ORG2 for v in v2)


def test_cross_org_asset_detail_is_404(client, db_session, as_user):
    _a1, a2 = _seed_two_orgs(db_session)

    # Org 1 user asking for org 2's asset summary must not see it.
    as_user(role=ROLE_ADMIN, org_id=ORG1)
    response = client.get(f"/assets/{a2.id}/summary")
    assert response.status_code == 404


def test_super_admin_sees_all_orgs(client, db_session, as_user):
    _seed_two_orgs(db_session)

    as_user(role=ROLE_SUPER_ADMIN, org_id=ORG1)
    assets = client.get("/assets").json()

    assert len(assets) == 2
    assert {a["org_id"] for a in assets} == {ORG1, ORG2}


# --- write scoping -----------------------------------------------------

def test_created_asset_lands_in_callers_org(client, db_session, as_user):
    _make_org2(db_session)

    as_user(role=ROLE_ADMIN, org_id=ORG2)
    created = client.post(
        "/assets",
        json={
            "name": "web",
            "asset_type": "server",
            "owner": "IT",
            "criticality": "High",
            "ip_address": "10.9.9.9",
            "environment": "prod",
        },
    )
    assert created.status_code == 200

    # Visible to org 2...
    assert len(client.get("/assets").json()) == 1

    # ...and not to org 1.
    as_user(role=ROLE_ADMIN, org_id=ORG1)
    assert client.get("/assets").json() == []


# --- organization management API --------------------------------------

def test_org_api_requires_super_admin(client, as_user):
    as_user(role=ROLE_ADMIN, org_id=ORG1)
    assert client.get("/organizations").status_code == 403


def test_super_admin_can_create_and_list_orgs(client, db_session, as_user):
    as_user(role=ROLE_SUPER_ADMIN, org_id=ORG1)

    created = client.post(
        "/organizations", json={"name": "Acme", "slug": "acme"}
    )
    assert created.status_code == 201
    assert created.json()["slug"] == "acme"

    slugs = {o["slug"] for o in client.get("/organizations").json()}
    assert "acme" in slugs
