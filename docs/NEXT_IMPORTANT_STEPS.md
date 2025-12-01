# Next important steps

This note highlights concrete next steps to keep the Echo monorepo healthy and actionable. These items focus on changes with clear user benefit and low coordination overhead.

## 1) Stabilize the CLI surfaces
- Add regression tests for `echo.echoctl` subcommands (`cycle`, `health`, `plan`, `wish`) covering happy paths and representative error cases.
- Create short usage recipes in `docs/REPO_NAVIGATOR.md` that mirror the most common CLI flows (cycle, health snapshot, wish capture).
- Provide a `make echoctl-smoke` target that runs a minimal CLI sanity check without needing network access.

## 2) Ship a lightweight observability bundle
- Add a `scripts/observability_snapshot.py` helper that emits CPU, process, and node counts to stdout for quick troubleshooting.
- Wire the script into `Makefile` via `make observability-snapshot` so it is discoverable for on-call rotations.
- Include a sample JSON output in `docs/observability.md` to keep expectations consistent across environments.

## 3) Harden provenance and release artifacts
- Add a signed checksum manifest for the `artifacts/` payloads (use `sha256sum` with a README describing how to verify downloads).
- Update `RELEASE_PROVENANCE.json` with a short checklist describing the verification path for new drops.
- Automate checksum regeneration in CI by extending the existing release workflow (fail the job when artifacts change without updated manifests).

## 4) Reduce onboarding friction
- Provide a `scripts/bootstrap_env.py` that installs dev extras, verifies Python version, and prints next steps.
- Add a 5-minute quickstart in `docs/REPO_OVERVIEW.md` that chains the bootstrap script, `echoctl --help`, and the observability snapshot.
- Offer a concise glossary appendix in `docs/REPO_NAVIGATOR.md` for frequently referenced Echo terms.
