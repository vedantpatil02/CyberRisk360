"""
CyberRisk360

Purpose:
Derive risk-register entries automatically from an asset's
vulnerabilities.

One aggregate risk is maintained per asset (source="auto"): every
vulnerability on the asset links to it via `risk_id`, its impact comes
from the asset's criticality, its likelihood from the asset's worst
finding, and it is assigned to the asset's owner. Re-running is
idempotent - the existing auto risk is updated in place rather than
duplicated - so it stays current as findings are imported or closed.

Manual risks (source="manual") are never touched by this engine.
"""

from app.repositories.vulnerabilities.vulnerability_repository import (
    get_by_asset
)
from app.repositories.risks.risk_repository import (
    get_auto_risk_by_asset,
    create_risk,
    update_risk,
)
from app.services.risks.risk import (
    calculate_risk_score,
    calculate_risk_level,
)


DEFAULT_OWNER = "Unassigned"

# Asset criticality -> business impact (1-5). Unknown/blank defaults to
# medium so a risk is never silently understated.
IMPACT_BY_CRITICALITY = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
}
DEFAULT_IMPACT = 3

# Vulnerability severity -> likelihood (1-5), driven by the asset's
# single worst finding.
LIKELIHOOD_BY_SEVERITY = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
}
DEFAULT_LIKELIHOOD = 1

# Ordering used to pick the "worst" severity on an asset.
SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _impact_from_criticality(criticality):
    return IMPACT_BY_CRITICALITY.get(
        (criticality or "").lower(), DEFAULT_IMPACT
    )


def _worst_severity(vulnerabilities):
    worst = None
    worst_rank = 0

    for vulnerability in vulnerabilities:
        severity = (vulnerability.severity or "").lower()
        rank = SEVERITY_RANK.get(severity, 0)

        if rank > worst_rank:
            worst_rank = rank
            worst = severity

    return worst


def _severity_counts(vulnerabilities):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for vulnerability in vulnerabilities:
        severity = (vulnerability.severity or "").lower()
        if severity in counts:
            counts[severity] += 1

    return counts


def generate_risk_for_asset(db, asset, commit: bool = True):
    """
    Create or update the auto risk for one asset from its current
    vulnerabilities, and link those vulnerabilities to it.

    Returns the risk, or None if the asset has no vulnerabilities.
    """

    vulnerabilities = get_by_asset(db, asset.id, org_id=asset.org_id)

    if not vulnerabilities:
        return None

    impact = _impact_from_criticality(asset.criticality)
    likelihood = LIKELIHOOD_BY_SEVERITY.get(
        _worst_severity(vulnerabilities), DEFAULT_LIKELIHOOD
    )
    score = calculate_risk_score(impact, likelihood)
    level = calculate_risk_level(score)

    owner = asset.owner or DEFAULT_OWNER
    asset_label = asset.name or asset.ip_address or f"asset {asset.id}"

    counts = _severity_counts(vulnerabilities)
    title = f"Aggregate vulnerability risk: {asset_label}"
    description = (
        f"Auto-generated from {len(vulnerabilities)} vulnerabilities on "
        f"{asset_label} "
        f"(critical={counts['critical']}, high={counts['high']}, "
        f"medium={counts['medium']}, low={counts['low']})."
    )

    fields = {
        "title": title,
        "description": description,
        "impact": impact,
        "likelihood": likelihood,
        "risk_score": score,
        "risk_level": level,
        "owner": owner,
    }

    existing = get_auto_risk_by_asset(db, asset.id, org_id=asset.org_id)

    if existing:
        # Don't clobber a manually-set treatment status (e.g. Accepted).
        risk = update_risk(db, existing, fields)
    else:
        risk = create_risk(
            db,
            asset_id=asset.id,
            source="auto",
            org_id=asset.org_id,
            **fields,
        )

    # Link every vulnerability on the asset to this risk.
    changed = False
    for vulnerability in vulnerabilities:
        if vulnerability.risk_id != risk.id:
            vulnerability.risk_id = risk.id
            changed = True

    if changed and commit:
        db.commit()

    return risk


def generate_risks_for_assets(db, assets):
    """
    Generate/update auto risks for a collection of assets. Returns the
    number of assets for which a risk was produced.
    """

    generated = 0

    for asset in assets:
        if generate_risk_for_asset(db, asset) is not None:
            generated += 1

    return generated
