# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace/vault_v1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY vault_v1/pyproject.toml ./
COPY vault_v1/requirements.lock ./

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir watchfiles uvicorn[standard] \
    && pip install --no-cache-dir -r requirements.lock

FROM base AS dev

COPY vault_v1 /workspace/vault_v1

RUN pip install --no-cache-dir -e .[dev]

ENV PYTHONPATH=/workspace/vault_v1

EXPOSE 8080

CMD [
    "uvicorn",
    "vault.api.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8080",
    "--reload",
    "--reload-dir",
    "/workspace/vault_v1"
]
