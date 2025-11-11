# Architecture Overview

```text
content_vault/
├── ci/
│   └── github/workflows/ci.yml           # Automated quality and deployment guardrails
├── configs/
│   ├── config.v1.yaml                    # Bootstrap configuration (JSON-in-YAML)
│   ├── config.v2.json                    # Active configuration
│   ├── config.latest.json                # Pointer to latest release
│   └── dependencies.yaml                 # Runtime and service dependencies
├── database/
│   ├── schema.sql                        # Relational schema for metadata + blobs
│   └── migrations/001_init.sql           # Re-playable migration artifact
├── docs/
│   ├── architecture.md                   # This document
│   ├── api_routes.md                     # Route reference with semantics
│   ├── flow.md                           # Flow chart of ingestion & retrieval
│   ├── usage.md                          # Quick-start and operations guide
│   ├── versioning.md                     # Configuration lifecycle documentation
│   └── blueprint.md                      # Mini-platform blueprint tying layers together
├── scripts/
│   ├── bootstrap.sh                      # Environment bootstrap with safety checks
│   ├── run_server.sh                     # Convenience runner for the API server
│   └── update_config_changelog.py        # Event-driven config changelog automation
├── schema/config.schema.json             # JSON Schema for config validation
├── src/
│   ├── vault_api/                        # Backend API implementation
│   │   ├── main.py                       # HTTP entrypoint & request handling
│   │   ├── config.py                     # Config discovery utilities
│   │   ├── models.py                     # Data models for API payloads
│   │   ├── routers/vault.py              # Route definitions
│   │   └── services/                     # Storage, metadata, journal services
│   └── vault_config/                     # Event-driven configuration system
│       ├── loader.py                     # Loader + validation + changelog automation
│       └── events.py                     # Version tracking + rollback registry
└── tests/                                # Automated verification
    ├── test_api.py                       # API smoke & dedupe tests
    └── test_config.py                    # Config loader + rollback tests
```

## System Pillars

- **Backend API** – Lightweight HTTP server using the standard library to expose
  `/vault` routes. It layers routing logic over modular services for storage,
  metadata indexing, and change journaling.
- **Database Schema** – SQL schema defines durable tables mirroring the in-memory
  services and enabling real-world deployment targets (PostgreSQL or SQLite).
- **CI/CD Pipeline** – GitHub Actions workflow linting, testing, and packaging the
  blueprint to guarantee repeatable builds.
- **Documentation** – Markdown-based documentation communicates architecture,
  flows, and operational procedures supported by ASCII/Mermaid diagrams.
- **Configuration Control Plane** – JSON/YAML-driven configuration with schema
  enforcement, dependency tracking, and automated changelog updates.
- **Operational Tooling** – Shell and Python scripts bootstrap environments,
  update configuration changelog entries, and run the API for local testing.
