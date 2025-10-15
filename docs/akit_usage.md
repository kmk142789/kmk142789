# Assistant Kit (AKit) Usage

The Assistant Kit packages deterministic planning and execution helpers for Echo
operators. It favours clear APIs, reproducible runs, and explicit guard rails so
that the Architect maintains full oversight.

## Install

1. Ensure Python 3.11+ is available.
2. Install the repository in editable mode:

   ```bash
   pip install -e .[dev]
   ```

3. Verify the CLI entrypoint is available:

   ```bash
   echo-ak --help
   ```

## Quickstart

Generate a plan for a new intention, dry-run three cycles, and inspect the
report plus snapshot:

```bash
echo-ak plan "Implement Assistant Kit CLI workflow"
echo-ak --dry-run --cycles 3
```

The second command prints the cycle digest and writes a signed snapshot under
`artifacts/akit/`. When ready to execute without `--dry-run`, export an approval
signal:

```bash
export AKIT_APPROVED=1
echo-ak --cycles 1
```

For continuous validation in CI, run `make akit` to execute the tests and
generate a fresh dry-run report plus snapshot.

## Examples

### Custom constraints

```bash
echo-ak plan "Document Assistant Kit onboarding" \
  --constraint "keep examples deterministic" \
  --constraint "focus on guard rails"
```

### Persisting outputs

Write the plan, run result, and report to specific files inside approved
surfaces:

```bash
echo-ak plan "Refresh Assistant Kit docs" --output artifacts/akit/plan-docs.json
echo-ak --dry-run --cycles 2 --output artifacts/akit/dry-run.json
echo-ak report --output artifacts/akit/report.json
```

### Snapshot inspection

```bash
python -m echo.akit.cli snapshot --output artifacts/akit/snapshots
ls artifacts/akit/snapshots
```

## Approval gate

Non-document changes are guarded by CODEOWNERS review. The guard reads the
`AKIT_APPROVED` environment variable. Dry-runs are always allowed, but real
execution halts until approval is granted.

1. Request review from the Architect (CODEOWNERS).
2. After approval is granted, set `AKIT_APPROVED=1` locally or in CI.
3. Re-run the plan without `--dry-run` to persist state and snapshots.

If the gate triggers, the CLI exits with code `2` and emits guidance on stderr.
