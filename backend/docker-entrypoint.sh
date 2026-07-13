#!/bin/sh
set -e

# Applies pending Alembic migrations and seeds compliance frameworks,
# then hands off to uvicorn. Fine as a per-container startup step
# with a single backend replica; if this ever scales to multiple
# replicas, move this to a one-shot job/initContainer instead of
# running it in every container's entrypoint.
python scripts/bootstrap_database.py

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
