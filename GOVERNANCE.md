# Echo Governance

- **Stewards:** @kmk142789420 and the `echo-bot` automation account retain final
  merge authority.  All substantive changes flow through reviewed pull requests
  with CODEOWNERS approval.
- **Decision Model:** We use a lightweight RFC process.  Open an issue labelled
  `governance` describing the proposal, gather feedback, and close it by linking
  the implementing pull request once consensus is reached.
- **Release Cadence:** Stable tags cut from `main` after CI + Mirror sync pass.
  Package-specific release notes live under `docs/releases/`.
- **Incident Response:** Follow [`SECURITY_RESPONSE.md`](SECURITY_RESPONSE.md)
  for vulnerability disclosures.  Operational incidents are logged in
  `ops/incident-journal.md` (create it on first use).
