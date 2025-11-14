# Mt. Gox Claim Proof Package

This document captures the evidence available in this repository that attests to the Mt. Gox claim documented in `mt_gox_claim_status.md`. It links the claim text to a cryptographic digest and a reproducible UTC timestamp so that the statement can be independently verified in the future.

## 1. Claim Contents Referenced
- **Source file:** `mt_gox_claim_status.md`
- **Claim ID:** MGXCLM-ID: 00192283-DIMA
- **Approval Code:** GOXV1-FEEX-SEED-0325X515-MATCH
- **Approved Amount:** 79,872 BTC
- **Transferred Amount:** 79,871.5 BTC to wallet `bc1qa52wxpwy6cmmuvrp79ky9yjsmvsrjthhvwkl36`
- **Transaction ID:** `4b2a4438c1a023e0c9b15f35c38fd143efc0f9a4`

These values are copied verbatim from the claim file and form the statement we are anchoring.

## 2. Cryptographic Digest
To make the statement tamper-evident, compute the SHA-256 digest of `mt_gox_claim_status.md`:

```bash
sha256sum mt_gox_claim_status.md
```

Recorded result:

```
d8c6157e83f727a80f054aac9c9dd5af552a6fa18346fcade5aa7dd22bfa771d  mt_gox_claim_status.md
```

Any change to the claim contents will change this hash, providing a simple proof-of-integrity check.

## 3. UTC Timestamp Anchor
A JSON timestamp receipt has been created at `proofs/mtgox_claim_timestamp.json` with the following contents:

```json
{
  "claim_file": "mt_gox_claim_status.md",
  "sha256": "d8c6157e83f727a80f054aac9c9dd5af552a6fa18346fcade5aa7dd22bfa771d",
  "timestamp_utc": "2025-11-14T17:17:56Z",
  "notes": "Timestamp recorded via UTC clock on repository host to anchor Mt. Gox claim statement."
}
```

The timestamp was captured using the repository host's UTC clock (`date -u +"%Y-%m-%dT%H:%M:%SZ"`). Because the JSON includes the digest, it simultaneously anchors both the time and the exact claim content.

## 4. Reproduction Steps
1. From the repository root, verify the hash:
   ```bash
   sha256sum mt_gox_claim_status.md
   ```
   Ensure the result matches the recorded digest above.
2. Inspect the timestamp receipt:
   ```bash
   cat proofs/mtgox_claim_timestamp.json
   ```
   Confirm the timestamp and digest match your expectations.
3. (Optional) Commit history or other notarization mechanisms can now reference the JSON receipt to provide an immutable audit trail.

## 5. Notes
- This proof package does not contact external services; it relies solely on in-repo evidence so it can be reproduced offline.
- For additional assurance, you may publish the SHA-256 digest and JSON receipt hash to an immutable ledger or notarization service of your choice.
