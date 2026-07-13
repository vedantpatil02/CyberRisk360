FROM python:3.13-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY frameworks/ ./frameworks/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY docker-entrypoint.sh .

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app \
    && chmod +x docker-entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
