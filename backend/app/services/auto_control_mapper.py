for vulnerability in imported_vulnerabilities:

    controls = suggest_controls(
        vulnerability.title
    )

    create risk_control_mapping