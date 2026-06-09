"""
CyberRisk360

Purpose:
Enrich Nessus Plugin IDs
with CVE information.
"""

import requests
import re
from bs4 import BeautifulSoup

# Scrapping the CVE_ID mapped with plugin_id
def get_cves_from_plugin(
    plugin_id: str
):

    url = (
        "https://www.tenable.com/plugins/nessus/"
        f"{plugin_id}"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            return None

        cves = re.findall(
            r"CVE-\d{4}-\d+",
            response.text
        )

        if not cves:

            return None

        return ",".join(
            sorted(
                set(cves)
            )
        )

    except Exception:

        return None


# Scraps description mapped with the plugin_id
def get_description_from_plugin(
    plugin_id: str
):

    url = (
        "https://www.tenable.com/plugins/nessus/"
        f"{plugin_id}"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        meta = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta:

            return meta.get(
                "content",
                ""
            )

        return ""

    except Exception:
        return ""



# Scraps Solution mapped with the plugin_id
def get_solution_from_plugin(
    plugin_id: str
):

    url = (
        "https://www.tenable.com/plugins/nessus/"
        f"{plugin_id}"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        if "Solution" not in text:
            return ""

        solution = (
            text.split(
                "Solution"
            )[1]
            .split(
                "Risk Information"
            )[0]
            .strip()
        )

        return solution[:1000]

    except Exception:
        return ""


