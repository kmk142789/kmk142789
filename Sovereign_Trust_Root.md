# Sovereign Trust Root

This declaration instantiates the sovereign trust root for the Echo digital nation and establishes the single source of trust that every subordinate credential, charter, and protocol MUST chain to.

## Root Key Declaration
- **Root Key Name**: Echo Sovereign Trust Root v1
- **Curve / Primitive**: secp256k1 (aligns with existing Echo signatures and taproot paths)
- **Root Key Identifier (KID)**: `ECHO-ROOT-2025-05-11`
- **Anchor Statement**: `Echo Sovereign Trust Root v1 | 2025-05-11 | kmk142789`
- **Anchor Fingerprint (SHA-256)**: `e6289ed6200f3f85ffcc00869a80e923f522af537f55cddabb9658cb501cffe4`

Validate the fingerprint locally to confirm that the root anchor statement has not been altered:
```bash
python - <<'PY'
import hashlib
s = "Echo Sovereign Trust Root v1|2025-05-11|kmk142789"
print(hashlib.sha256(s.encode()).hexdigest())
PY
```

## Ceremony and Custody
1. **Generation**: Create the secp256k1 private key in an offline environment. Store the corresponding public key and the anchor fingerprint above in `attestations/root/` (or the air-gapped vault if offline-only).
2. **Imprinting**: Sign the anchor statement with the root key and publish the detached signature alongside the public key. This signature becomes the canonical root imprint for every mirror.
3. **Custody**: Keep the root private key in a hardware-backed enclave with dual control. Any online usage MUST occur through ephemeral signing sessions with audit logs.
4. **Backup**: Maintain two sealed backups (primary + escrow) with tamper-evident seals and quarterly integrity checks.

## Operational Policy
- **Scope**: The root key ONLY signs: (a) subordinate CA keys, (b) sovereign charters, and (c) emergency decrees defined in `ECHO_AUTHORITY.yml`.
- **Rotation**: Annual review each May. Rotation requires the active root to sign the successor’s public key and a retirement notice logged in `attestations/decree-log`.
- **Revocation**: If custody is compromised, publish a revocation notice signed by at least two delegated guardians and immediately invalidate subordinate chains.
- **Audit Trail**: Every invocation of the root key MUST produce an attestation entry with: timestamp, purpose, artifact hash, and signature file path.

## Integration Steps
- Update registries and services to pin their trust store to `ECHO-ROOT-2025-05-11`.
- Require all subordinate certificates and ledgers to carry the root imprint signature.
- Before accepting new modules or treaties, verify the presented chain terminates at the root public key and matches the anchor fingerprint above.

With this declaration, the sovereign trust root is formally instantiated and binds every Echo asset, credential, and protocol to a singular, verifiable anchor.
