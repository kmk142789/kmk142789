# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir fastapi uvicorn[standard] watchfiles pydantic rich

FROM base AS dev

WORKDIR /workspace/identity_bridge

ENV PYTHONPATH=/workspace/identity_bridge:/workspace/modules:/workspace/packages/core/src

CMD [
    "uvicorn",
    "identity_bridge.app:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8081",
    "--reload",
    "--reload-dir",
    "/workspace/identity_bridge",
    "--reload-dir",
    "/workspace/modules",
    "--reload-dir",
    "/workspace/packages/core/src"
]
