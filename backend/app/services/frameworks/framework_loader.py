"""
CyberRisk360

Purpose:
Load framework data from JSON files.
"""

import json


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