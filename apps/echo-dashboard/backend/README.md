# Echo Dashboard API

An Express service that exposes Echo artifacts for the unified dashboard.

## Features

- Lists Echo Computer logs and puzzle solution manuscripts.
- Executes a curated set of `echo_cli` commands through a sandboxed runner.
- Stores Neon API keys encrypted with AES-256-GCM before persisting to Postgres.

## Configuration

| Variable | Purpose |
| --- | --- |
| `ECHO_DASHBOARD_PORT` | HTTP port (defaults to `5050`). |
| `ECHO_DASHBOARD_PYTHON` | Python binary used for CLI execution (defaults to `python3`). |
| `ECHO_DASHBOARD_TIMEOUT_MS` | Max execution time for CLI commands. |
| `NEON_DATABASE_URL` | Connection string for the Neon Postgres instance. |
| `NEON_KEY_ENCRYPTION_KEY` | Shared secret used for envelope encryption. Must be at least 16 characters. |
| `PGSSLMODE` | Set to `disable` to skip TLS (not recommended). |

When database variables are omitted, Neon key endpoints respond with `503` and the rest of the API remains functional.

## Development

```bash
node apps/echo-dashboard/backend/server.mjs
```

The service expects to be executed from the repository root so it can resolve the `logs/`, `puzzle_solutions/`, and `echo_cli/` modules.
