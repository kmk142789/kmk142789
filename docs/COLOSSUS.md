# COLOSSUS PRIME — MASTER BRIEF

This repository contains the core building blocks for the Colossus platform. It
is designed to remain deterministic, reproducible, and verifiable using only the
Python 3.11 standard library by default. Optional extras live behind dedicated
Python extras.

## Quickstart (60 seconds)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make bootstrap
```

The `make bootstrap` target prepares the required directory structure and copies
baseline schema files into place.

## Packages

* `colossus.core`: foundational utilities (identifiers, hashing, filesystem,
  schema helpers).
* `schemas/`: strict JSON Schema definitions for every artifact type.
* `docs/`: operational documentation for running Colossus.

Each subsequent pull request in the Colossus roadmap layers more functionality
on top of these primitives.
