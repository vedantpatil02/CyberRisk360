"""
CyberRisk360

Purpose:
Look up a CWE (Common Weakness Enumeration) ID against a small, curated
static reference catalog (frameworks/common/cwe_catalog.json) - real
MITRE text for the CWE IDs this codebase's own mapping engine already
references across its mapping_rules.json files. Unlike CISA KEV/EPSS,
CWE definitions barely change, so this is a checked-in file, not a
live per-request API call.
"""

from app.core.constants import FRAMEWORKS_DIR
from app.services.frameworks.framework_loader import load_framework

_CATALOG_PATH = FRAMEWORKS_DIR / "common" / "cwe_catalog.json"


def _load_catalog():
    return {
        entry["cwe_id"]: entry
        for entry in load_framework(_CATALOG_PATH)
    }


def get_cwe_info(cwe_id: str):
    """
    Return {"cwe_id", "name", "description"} for a curated CWE id, or
    None if it isn't in the catalog. Callers still know the real cwe_id
    even on a miss (e.g. to build a definitions-page URL) - this only
    supplies the name/description text that's been verified against a
    real MITRE source.
    """

    return _load_catalog().get(cwe_id)
