"""
CyberRisk360

Purpose:
Generic, framework-agnostic engine that maps vulnerabilities to
compliance controls using CVE, CWE, Plugin ID, and keyword rules.

Rules are loaded from every framework's mapping_rules.json (found via
the same discover_frameworks() scan used to import frameworks/controls)
and merged into one ruleset, so this module never references a
specific framework or control set by name.
"""

import json
import re
from pathlib import Path

from app.core.constants import (
    FRAMEWORKS_DIR,
    MATCH_TYPE_CVE,
    MATCH_TYPE_CWE,
    MATCH_TYPE_PLUGIN_ID,
    MATCH_TYPE_KEYWORD,
    MAPPING_CONFIDENCE_BY_MATCH_TYPE,
    MAPPING_STATUS_PENDING
)

from app.services.frameworks.framework_loader import discover_frameworks

from app.repositories.controls.control_repository import (
    get_control_by_code
)

from app.repositories.vulnerability_control_mappings.mapping_repository import (
    mapping_exists,
    create_mapping
)

from app.repositories.vulnerability_control_mappings.mapping_history_repository import (
    record_history
)

_CWE_PATTERN = re.compile(r"CWE-\d+", re.IGNORECASE)

# Checked in this order so that, when a vulnerability matches the
# same control via more than one rule, the highest-confidence match
# type is the one that wins (mapping_exists blocks the lower-
# confidence duplicates that would otherwise follow).
_MATCH_TYPE_ORDER = (
    MATCH_TYPE_CVE,
    MATCH_TYPE_PLUGIN_ID,
    MATCH_TYPE_CWE,
    MATCH_TYPE_KEYWORD
)

_EMPTY_RULES = {
    MATCH_TYPE_CVE: {},
    MATCH_TYPE_CWE: {},
    MATCH_TYPE_PLUGIN_ID: {},
    MATCH_TYPE_KEYWORD: {}
}


def load_rules(frameworks_dir=FRAMEWORKS_DIR):
    """
    Merge mapping_rules.json from every discovered framework version
    into one {match_type: {identifier: [control_codes]}} ruleset.

    Frameworks with no mapping_rules.json, an empty one, or invalid
    JSON are skipped silently - rules are optional data, not a
    requirement for a framework to be valid.
    """

    merged = {match_type: {} for match_type in _EMPTY_RULES}

    for info in discover_frameworks(frameworks_dir).values():

        rules_path = Path(info["version_dir"]) / "mapping_rules.json"

        if not rules_path.exists() or rules_path.stat().st_size == 0:
            continue

        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        for match_type, entries in rules.items():

            if match_type not in merged or not isinstance(entries, dict):
                continue

            for identifier, control_codes in entries.items():
                key = identifier.strip().lower()
                merged[match_type].setdefault(key, [])
                merged[match_type][key].extend(control_codes)

    return merged


def _extract_cve_ids(vulnerability):
    cve_id = getattr(vulnerability, "cve_id", None)

    if not cve_id:
        return []

    return [
        cve.strip()
        for cve in re.split(r"[,\s]+", cve_id)
        if cve.strip()
    ]


def _extract_cwe_ids(vulnerability):
    text = " ".join(
        part for part in (
            getattr(vulnerability, "title", None),
            getattr(vulnerability, "description", None)
        ) if part
    )

    # Dedupe while preserving first-seen order
    seen = []

    for match in _CWE_PATTERN.findall(text):
        cwe = match.upper()
        if cwe not in seen:
            seen.append(cwe)

    return seen


def find_candidate_matches(vulnerability, rules=None):
    """
    Return [(match_type, matched_value, control_code), ...] candidates
    for a vulnerability. Pure/DB-free, so it's cheap to unit test with
    a plain object exposing title/description/cve_id/plugin_id.
    """

    rules = rules if rules is not None else load_rules()

    candidates = []

    for cve in _extract_cve_ids(vulnerability):
        for control_code in rules[MATCH_TYPE_CVE].get(cve.lower(), []):
            candidates.append((MATCH_TYPE_CVE, cve, control_code))

    plugin_id = getattr(vulnerability, "plugin_id", None)

    if plugin_id:
        plugin_id = str(plugin_id).strip()
        for control_code in rules[MATCH_TYPE_PLUGIN_ID].get(plugin_id.lower(), []):
            candidates.append((MATCH_TYPE_PLUGIN_ID, plugin_id, control_code))

    for cwe in _extract_cwe_ids(vulnerability):
        for control_code in rules[MATCH_TYPE_CWE].get(cwe.lower(), []):
            candidates.append((MATCH_TYPE_CWE, cwe, control_code))

    text = " ".join(
        part for part in (
            getattr(vulnerability, "title", None),
            getattr(vulnerability, "description", None)
        ) if part
    ).lower()

    for keyword, control_codes in rules[MATCH_TYPE_KEYWORD].items():
        if keyword in text:
            for control_code in control_codes:
                candidates.append((MATCH_TYPE_KEYWORD, keyword, control_code))

    order = {match_type: index for index, match_type in enumerate(_MATCH_TYPE_ORDER)}
    candidates.sort(key=lambda candidate: order[candidate[0]])

    return candidates


def map_vulnerability_to_controls(db, vulnerability, rules=None):
    """
    Find candidate control matches for a vulnerability and persist
    them as pending mappings with a confidence score, each backed by
    a "created" history entry. Mappings require manual approval
    (see mapping_service.review_mapping) before they should count
    toward compliance reporting.

    Does not commit - the caller controls the transaction boundary,
    same as the rest of the import pipeline.
    """

    created_mappings = []

    for match_type, matched_value, control_code in find_candidate_matches(vulnerability, rules):

        control = get_control_by_code(db, control_code)

        if not control:
            continue

        if mapping_exists(db, vulnerability.id, control.id):
            continue

        mapping = create_mapping(
            db,
            vulnerability_id=vulnerability.id,
            control_id=control.id,
            org_id=vulnerability.org_id,
            match_type=match_type,
            matched_value=matched_value,
            confidence_score=MAPPING_CONFIDENCE_BY_MATCH_TYPE[match_type],
            status=MAPPING_STATUS_PENDING
        )

        record_history(
            db,
            mapping_id=mapping.id,
            action="created",
            new_status=MAPPING_STATUS_PENDING,
            org_id=vulnerability.org_id,
            actor="system",
            note=f"{match_type} match on {matched_value}"
        )

        created_mappings.append(mapping)

    return created_mappings
