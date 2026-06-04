"""
CyberRisk360

Purpose:
Parse Nessus CSV reports.
"""

import csv


def parse_nessus_csv(
    file_path: str
):
    """
    Parse Nessus CSV file
    and return findings.
    """

    findings = []

    with open(
        file_path,
        newline="",
        encoding="utf-8"
    ) as csv_file:

        reader = csv.DictReader(
            csv_file
        )

        for row in reader:

            findings.append(
                row
            )

    return findings