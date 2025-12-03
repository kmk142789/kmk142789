# Echo Core

The core package contains the primary Echo runtime, including the CLI, bridge
adapters, attestation utilities, and the `echo` Python package.  Install it in
editable mode while working inside the monorepo:

```bash
python -m pip install -e .[dev]
```

Then you can explore the CLI:

```bash
python -m echo.cli --help
python -m echo.echoctl cycle
python packages/core/src/adaptive_intelligence_matrix.py --emit-markdown out/matrix.md
```

Need the legacy manifest-only helper? Invoke `python -m echo.manifest_cli` or the
`echo-manifest` console script for that streamlined workflow.

The source code lives under `packages/core/src/` and mirrors the historical
`echooo` repository layout while keeping full commit history via `git subtree`.

## Adaptive Intelligence Matrix

Use `adaptive_intelligence_matrix` when you need a quick synthesis of the
continuum pulse, TODO/FIXME/HACK density, and the published plan:

```bash
python packages/core/src/adaptive_intelligence_matrix.py --emit-json out/matrix.json
```

The module fuses the live telemetry artifacts (`pulse_history.json`,
`roadmap_summary.json`, and `docs/NEXT_CYCLE_PLAN.md`) into composite scores for
automation pressure, adaptability, and overall signal health. The JSON output is
ideal for dashboards while the default console view surfaces recommendations
for tightening operational loops. The latest build also emits an alert feed that
pulls the highest-severity signals (stale pulses, TODO pressure, or missing
success criteria) into a concise triage table in both the Markdown and JSON
renderings.
