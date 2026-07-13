"""
CyberRisk360

Purpose:
Application configuration settings.
"""

import os

# Dev-only fallback; set a real SECRET_KEY in the environment for
# any non-local deployment so JWTs can't be forged from source.
SECRET_KEY = os.environ.get("SECRET_KEY", "cyberrisk360-secret-key")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60