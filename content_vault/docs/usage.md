# Usage Guide

## Prerequisites

- Python 3.11+

## Bootstrap

```bash
cd content_vault
python scripts/update_config_changelog.py
python -m vault_api.main
```

The server listens on `127.0.0.1:8080` by default. Override using environment variables:

```bash
export VAULT_HOST=0.0.0.0
export VAULT_PORT=9000
export VAULT_CONFIG_PATH=$(pwd)/configs/config.v2.json
python -m vault_api.main
```

## Example Interactions

```bash
curl -X POST http://127.0.0.1:8080/vault/items \
  -H 'Content-Type: application/json' \
  -d '{"content": "hello", "metadata": {"collection": "demo"}}'

curl "http://127.0.0.1:8080/vault/items?collection=demo"
```

## Tests

```bash
cd content_vault
python -m pytest
```

The tests cover:

- Deduplication and metadata indexing in the API layer.
- Configuration validation, version tracking, and rollback logic.
