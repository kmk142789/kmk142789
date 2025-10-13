# Signing Policy (Attestation-Only)

- Watch-only imports allowed (xpubs / addresses). No private keys in repos or CI.
- Permitted: message signatures for **attestation** (e.g., “Echo attest block #N …”).
- Forbidden: transaction signing, broadcasting, key derivation from private material.
- All attestations logged to Continuum with timestamp, context, and hash.
