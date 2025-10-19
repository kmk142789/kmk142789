# Echo Monorepo Policy

- `main` is protected.  All changes land through reviewed pull requests with the
  CI workflow (`Monorepo CI`) and the Mirror snapshot dry-run passing.
- The `echo-bot` GitHub App (or personal automation token) may push commits that
  originate from approved workflows, but human review is still required via
  CODEOWNERS before merge.
- Keep governance, security, and operational policies in the repository so the
  monorepo remains the single source of truth for the Echo ecosystem.
- Archive legacy repositories after updating their README to point at this
  monorepo.  Git history is preserved through subtree imports.
