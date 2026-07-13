"""
CyberRisk360

Purpose:
Load framework data from JSON files, and discover which
frameworks/versions exist on disk.
"""

import json
from pathlib import Path


def load_framework(
    file_path: str
):
    """
    Load framework controls
    from JSON file.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def discover_frameworks(
    frameworks_dir
):
    """
    Scan frameworks_dir for every <framework>/<version>/metadata.json
    and return {short_name: {metadata_path, framework_path, version_dir}}.

    Purely structural: no framework name is ever referenced here, so
    dropping a new frameworks/<name>/<version>/ directory is enough
    for it to be picked up automatically.
    """

    discovered = {}

    frameworks_dir = Path(frameworks_dir)

    if not frameworks_dir.is_dir():
        return discovered

    for metadata_path in sorted(frameworks_dir.glob("*/*/metadata.json")):

        framework_path = metadata_path.parent / "framework.json"

        if not framework_path.exists():
            continue

        metadata = load_framework(metadata_path)

        short_name = metadata.get("short_name")

        if not short_name:
            continue

        discovered[short_name] = {
            "metadata_path": str(metadata_path),
            "framework_path": str(framework_path),
            "version_dir": str(metadata_path.parent)
        }

    return discovered