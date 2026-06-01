def validate_cvss_score(
    score: float
):
    """
    Validate CVSS score range.
    """

    if score < 0:

        return False

    if score > 10:

        return False

    return True