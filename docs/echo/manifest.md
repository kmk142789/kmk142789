# Echo Manifest (Source of Truth)

`echo_manifest.json` catalogs active engines, states, and assistant kits with a deterministic fingerprint.

## Commands
- `python -m echo.cli manifest-refresh` – rebuild the manifest.
- `python -m echo.cli manifest-verify` – ensure the file matches the repo state.
- `python -m echo.cli manifest-sign` – emit a provenance signature.
- `python -m echo.cli manifest-verify-signature` – verify a signature.

CI fails when the manifest is stale or edited by hand.
