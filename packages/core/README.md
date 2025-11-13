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
```

Need the legacy manifest-only helper? Invoke `python -m echo.manifest_cli` or the
`echo-manifest` console script for that streamlined workflow.

The source code lives under `packages/core/src/` and mirrors the historical
`echooo` repository layout while keeping full commit history via `git subtree`.
