## Contributing to the Echo Monorepo

- Add or update attestations in `/attestations/` (they must validate against the
  JSON schemas in `/schema/`).
- Place Python sources inside the appropriate package under `packages/`.
  Shared runtime code lives in `packages/core/src`.
- Run `python -m pip install -e .[dev]` followed by `pytest -q` before opening a
  pull request.
- The GitHub Actions workflows (`Monorepo CI` and `Mirror Sync`) must pass before
  merging.
