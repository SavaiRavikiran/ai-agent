# Multi-stage build for AI DevOps Agent
FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir poetry
WORKDIR /app
COPY pyproject.toml ./
RUN poetry config virtualenvs.in-project true \
    && poetry lock --no-update 2>/dev/null || true \
    && poetry install --no-dev --no-interaction --no-root

FROM python:3.11-slim

RUN useradd --create-home --uid 1000 ai-agent
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY main.py ./
COPY agent ./agent
COPY tools ./tools
COPY rag ./rag
COPY watcher ./watcher
COPY api ./api
COPY config ./config

RUN mkdir -p /var/log/ai-agent /secrets /certs && chown -R ai-agent:ai-agent /var/log/ai-agent /app

USER ai-agent
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

ENTRYPOINT ["python", "main.py"]
