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
    && pip install --no-cache-dir watchfiles rich

FROM base AS dev

ENV PYTHONPATH=/workspace

CMD [
    "watchfiles",
    "--filter",
    "python",
    "python -m compliance.cli asterc:validate /workspace/identity",
    "compliance",
    "identity"
]
