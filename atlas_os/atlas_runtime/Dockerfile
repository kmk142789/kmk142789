# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/root-requirements.txt
COPY atlas_os/requirements.txt /tmp/atlas-os-requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /tmp/root-requirements.txt \
    && pip install --no-cache-dir -r /tmp/atlas-os-requirements.txt \
    && pip install --no-cache-dir watchfiles

FROM base AS dev

ENV PYTHONPATH=/workspace

CMD [
    "watchfiles",
    "--filter",
    "python",
    "pytest atlas_os/atlas_runtime/tests",
    "atlas_os/atlas_runtime",
    "tests"
]
