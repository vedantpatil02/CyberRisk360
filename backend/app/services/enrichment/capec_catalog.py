"""
CyberRisk360

Purpose:
Look up the CAPEC (Common Attack Pattern Enumeration and Classification)
attack pattern - and, where MITRE's own CAPEC data links one, the MITRE
ATT&CK technique(s) - for a CWE id, against a small curated static
reference catalog (frameworks/common/capec_catalog.json). Mirrors
cwe_catalog.py's shape: one dataset covers both CAPEC Mapping and MITRE
ATT&CK Mapping, since real CAPEC data already includes both a CWE
("Related Weaknesses") and an ATT&CK ("Taxonomy Mappings") linkage -
no separate ATT&CK ingestion needed. Static, not a live per-request
call - this reference data doesn't change day-to-day.
"""

from app.core.constants import FRAMEWORKS_DIR
from app.services.frameworks.framework_loader import load_framework

_CATALOG_PATH = FRAMEWORKS_DIR / "common" / "capec_catalog.json"

_CAPEC_URL_TEMPLATE = "https://capec.mitre.org/data/definitions/{number}.html"
_ATTACK_URL_TEMPLATE = "https://attack.mitre.org/techniques/{path}/"


def _load_catalog():
    return {
        entry["cwe_id"]: entry
        for entry in load_framework(_CATALOG_PATH)
    }


def _attack_url(technique_id: str) -> str:
    # MITRE's real URL scheme for sub-techniques uses a slash, not the
    # dot the technique id itself uses (e.g. T1110.001 ->
    # .../techniques/T1110/001/).
    return _ATTACK_URL_TEMPLATE.format(path=technique_id.replace(".", "/"))


def get_capec_for_cwe(cwe_id: str):
    """
    Return {"capec_id", "name", "description", "url", "attack_techniques":
    [{"id", "name", "url"}, ...]} for a curated CWE id, or None if it
    isn't in the catalog. `attack_techniques` is an empty list (not
    omitted) when the real CAPEC data has no ATT&CK linkage for this
    pattern - most of this curated set genuinely has none.
    """

    entry = _load_catalog().get(cwe_id)

    if not entry:
        return None

    number = entry["capec_id"].split("-")[-1]

    return {
        "capec_id": entry["capec_id"],
        "name": entry["name"],
        "description": entry["description"],
        "url": _CAPEC_URL_TEMPLATE.format(number=number),
        "attack_techniques": [
            {
                "id": technique["id"],
                "name": technique["name"],
                "url": _attack_url(technique["id"]),
            }
            for technique in entry["attack_techniques"]
        ],
    }
