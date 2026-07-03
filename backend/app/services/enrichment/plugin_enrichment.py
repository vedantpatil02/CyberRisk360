"""
CyberRisk360

Purpose:
Enrich Nessus Plugin IDs
with CVE information.
"""

import requests
import re
from bs4 import BeautifulSoup


PLUGIN_PAGE_CACHE = {}

def get_plugin_page(plugin_id):

    if plugin_id in PLUGIN_PAGE_CACHE:
        return PLUGIN_PAGE_CACHE[plugin_id]

    url = (
        "https://www.tenable.com/plugins/nessus/"
        f"{plugin_id}"
    )

    response = requests.get(
        url,
        timeout=10
    )

    if response.status_code != 200:
        return None

    PLUGIN_PAGE_CACHE[
        plugin_id
    ] = response.text

    return response.text


# Scrapping the CVE_ID mapped with plugin_id
def get_cves_from_plugin(
    plugin_id: str
):

    url = (
        "https://www.tenable.com/plugins/nessus/"
        f"{plugin_id}"
    )

    try:

        html = get_plugin_page(
            plugin_id
        )

        if not html:
            return None

        cves = re.findall(
            r"CVE-\d{4}-\d+",
            html
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

        html = get_plugin_page(
            plugin_id
        )

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
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

        html = get_plugin_page(
            plugin_id
        )

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
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


