# Development Data Recovery Runbook

This runbook documents how to replay migrations, seed deterministic fixtures, and
tear down local state for the Atlas core development environment.

## Prerequisites

* Python 3.11+
* Working directory at the repository root

All commands below are executed from the repository root unless stated otherwise.

## Apply schema migrations

Each persistence layer now exposes explicit migrations. Running the fixture
loaders automatically applies migrations, but they can be invoked individually
if needed:

```bash
python -c "from atlas.scheduler.migrations import apply_migrations; apply_migrations('data/scheduler.db')"
python -c "from federated_pulse.storage.migrations import apply_migrations; apply_migrations('.fpulse/pulse.db')"
python -c "from pulse_weaver.adapters.sqlite import SQLiteAdapter; from pulse_weaver.storage.migrations import apply_migrations; apply_migrations(SQLiteAdapter('data/pulse_weaver.db'))"
```

## Deterministic seeding

Use the orchestration helper to seed all fixtures in a single step. The command
creates the required directories, runs migrations, and loads the deterministic
fixture sets located in `fixtures/`.

```bash
python scripts/dev_orchestration.py seed
```

### Replay the seed cycle

Replay drops existing state and replays the deterministic fixtures:

```bash
python scripts/dev_orchestration.py replay
```

### Tear down state

To clear the databases without deleting the files, run:

```bash
python scripts/dev_orchestration.py teardown
```

If you need to remove the database files completely, delete `data/scheduler.db`,
`data/pulse_weaver.db`, and `.fpulse/pulse.db` after running the teardown.

## Retention policy enforcement

Retention policies for logs, metrics, and generated fixtures are defined in
`config/retention.json`. Enforce them on demand or in cron jobs with:

```bash
python scripts/enforce_retention.py
```

Use `--dry-run` to preview deletions:

```bash
python scripts/enforce_retention.py --dry-run
```

## Recovery checklist

1. Run `python scripts/dev_orchestration.py teardown` on the affected node.
2. Optionally delete lingering database files if they were corrupted.
3. Execute `python scripts/dev_orchestration.py seed` to rebuild deterministic
   state.
4. Restart services (e.g., `docker compose up atlas-core`).
5. Verify health by hitting the Atlas metrics endpoint (`http://localhost:9100`).
6. Enforce retention policies if the outage produced large log or fixture dumps:
   `python scripts/enforce_retention.py`.
