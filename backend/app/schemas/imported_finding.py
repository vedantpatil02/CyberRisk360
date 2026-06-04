from pydantic import BaseModel


class ImportedFinding(
    BaseModel):

    ip_address: str

    service: str

    version: str

    cve_id: str

    cvss_score: float

    severity: str

    description: str