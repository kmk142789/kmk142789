# Echo Nation v2 — Sovereign Identity Anchor

- Root DID: `did:echo:nation:v2:root`
- VC Issuer: `did:echo:nation:v2:issuer`
- Ledger: append-only event log for blueprints, rollouts, attestations, key rotations, and policy updates.
- Anchor Flow:
  1. Blueprint proposal recorded with hash + CID.
  2. Approval emits ledger anchor; rollout tasks must reference it.
  3. Worker attestations include anchor reference; invalid attestations are rejected.
- Key Management: supports rotation, revocation registry, and per-component capability keys.
