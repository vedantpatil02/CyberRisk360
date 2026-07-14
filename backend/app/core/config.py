"""
CyberRisk360

Purpose:
Application configuration settings.
"""

import os

from dotenv import load_dotenv

# Populates os.environ from a local .env file if present; never
# overrides a variable that's already set. Called here too (not just
# in db/database.py) since import order between the two isn't
# guaranteed across every entrypoint (e.g. alembic/env.py only
# imports app.db.database).
load_dotenv()

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

_DEV_DEFAULT_SECRET_KEY = "cyberrisk360-secret-key"
_PLACEHOLDER_SECRET_KEY = "changeme-generate-a-real-secret"

# Dev-only fallback; outside development/local/test this is enforced
# below rather than silently trusted, so JWTs can't be forged from a
# known/guessable key.
SECRET_KEY = os.environ.get("SECRET_KEY", _DEV_DEFAULT_SECRET_KEY)

if ENVIRONMENT.lower() not in ("development", "local", "test"):

    if SECRET_KEY in (_DEV_DEFAULT_SECRET_KEY, _PLACEHOLDER_SECRET_KEY):

        raise RuntimeError(
            "SECRET_KEY must be set to a real, unique secret when "
            "ENVIRONMENT is not 'development'/'local'/'test'. Generate "
            "one (e.g. `openssl rand -hex 32`) and set it in the "
            "environment - do not use the dev default or the "
            ".env.example placeholder."
        )

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Comma-separated list of origins allowed to make browser cross-origin
# requests. Empty by default - there's no frontend yet, and this only
# gates browser requests (server-to-server calls are unaffected).
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# When true, trust the `X-Forwarded-For` header for the client IP (rate
# limiting, audit trail). Enable ONLY when a trusted reverse proxy sits
# in front and sets this header - otherwise a client could spoof its IP.
# Default false: read the socket peer address directly.
TRUST_PROXY_HEADERS = (
    os.environ.get("TRUST_PROXY_HEADERS", "false").lower()
    in ("1", "true", "yes")
)

# Log level and format. LOG_FORMAT=json emits one JSON object per line
# (friendly to log aggregators); anything else uses a human-readable
# console format.
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "console").lower()