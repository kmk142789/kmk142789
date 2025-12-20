# Proof Snapshot Mechanism Design

## Overview
This design defines a **signed, replayable snapshot** mechanism for three artifact classes:

- **DNS state** (zones, DNSSEC material, registrar metadata)
- **Governance state** (policies, resolutions, votes, quorum proofs)
- **Hardware artifacts** (firmware, SBOM, measurement logs, TPM quotes)

Snapshots are **content-addressed**, **chained**, and **signed by thresholds of independent keys**, with public anchoring and transparency logs so **third parties can verify without trusting operators**.

## Goals
- **Replayable**: any verifier can reconstruct the exact snapshot from immutable inputs.
- **Tamper-evident**: any modification invalidates hashes/signatures.
- **Compositional**: each artifact type is independently verifiable.
- **Auditable provenance**: every snapshot references a previous snapshot hash.
- **Operator trust minimization**: use independent witnesses and public anchoring.

## Snapshot Bundle Layout
Each snapshot bundle is a directory (or tarball) with deterministic filenames:

```
proof_snapshot_<epoch>/
  manifest.json
  dns/
    zonefiles/
    dnssec/
    registrar.json
    dns_root.json
    merkle.json
  governance/
    resolutions.json
    votes.json
    quorum.json
    policy_hashes.json
    merkle.json
  hardware/
    firmware_manifest.json
    sbom.spdx.json
    measurements.json
    tpm_quotes.json
    device_roots.json
    merkle.json
  signatures/
    snapshot.dsse.json
    snapshot.signatures.json
  anchors/
    transparency_log.json
    opentimestamps.ots
```

### Deterministic Manifest
`manifest.json` is the canonical root that binds every artifact:

```json
{
  "snapshot_id": "2025-10-08T12:00:00Z",
  "previous_snapshot": "<sha256>",
  "created_at": "2025-10-08T12:00:00Z",
  "inputs": {
    "dns": {"root": "<sha256>", "merkle": "<sha256>"},
    "governance": {"root": "<sha256>", "merkle": "<sha256>"},
    "hardware": {"root": "<sha256>", "merkle": "<sha256>"}
  },
  "canonicalization": "rfc8785+jcs",
  "snapshot_root": "<sha256>",
  "metadata": {
    "operator": "<string>",
    "witness_set": ["<key-id>", "<key-id>"]
  }
}
```

- `snapshot_root` = SHA-256 of canonicalized `manifest.json`.
- `previous_snapshot` chains snapshots for replayable history.

## Canonicalization Rules
To ensure replayability, all JSON inputs are canonicalized:

- **RFC 8785 (JCS)** for JSON canonicalization.
- **Stable ordering** for file lists when building Merkle trees.
- **Content-addressed file names** (e.g., `sha256_<hash>.json`).

For non-JSON:
- DNS zone files must be normalized (whitespace, ordering, SOA serial normalization).
- Binary firmware is hashed directly (SHA-256), and referenced by hash.

## Artifact-Specific Inputs

### DNS
- Zone files in canonical format
- DNSSEC keys (`KSK`, `ZSK`) and DS records
- Registrar metadata (ownership, registrar proofs)

**DNS Merkle root** includes:
- `zonefiles/*`
- `dnssec/*`
- `registrar.json`
- `dns_root.json`

### Governance
- Resolutions (final text and version)
- Votes and cryptographic vote proofs
- Quorum calculations
- Policy hashes and amendments

**Governance Merkle root** includes:
- `resolutions.json`
- `votes.json`
- `quorum.json`
- `policy_hashes.json`

### Hardware
- Firmware manifest (version → hash)
- SBOM (SPDX)
- Measurements (PCR logs or equivalent)
- TPM quotes and device root certs

**Hardware Merkle root** includes:
- `firmware_manifest.json`
- `sbom.spdx.json`
- `measurements.json`
- `tpm_quotes.json`
- `device_roots.json`

## Signing Model
Snapshots are signed using a **threshold signature policy**:

- **Operator keys**: N-of-M required.
- **Independent witness keys**: at least K signatures required from 3rd-party witnesses.
- **Hardware attestation keys**: optional for device-bound artifacts.

Signatures are captured via **DSSE envelopes**:

- `snapshot.dsse.json` contains payload = `manifest.json`.
- `snapshot.signatures.json` contains key IDs and detached signatures.

This ensures signatures are bound to the snapshot hash and tamper-evident.

## Transparency and Anchoring
To minimize operator trust, each snapshot is anchored in public logs:

1. **Transparency log** (append-only): `transparency_log.json` includes a log proof.
2. **Open timestamp**: `opentimestamps.ots` anchors the manifest hash.
3. **Optional public blockchain anchor** (Bitcoin/Ethereum) for extra immutability.

## Replayability Guarantees
A verifier can:

1. Fetch the snapshot bundle by `snapshot_id`.
2. Canonicalize and hash each artifact.
3. Rebuild Merkle roots per artifact category.
4. Reconstruct `manifest.json` and compute `snapshot_root`.
5. Validate signatures and thresholds.
6. Verify `previous_snapshot` chain.
7. Validate transparency log inclusion and OpenTimestamps proof.

If any step fails, the snapshot is invalid.

## Verification Without Operator Trust
The mechanism avoids trusting operators by:

- **Multiple independent witnesses** signing each snapshot.
- **Public anchoring** of snapshot hash in multiple immutable channels.
- **Deterministic reconstruction** of all inputs from public sources.
- **Replayable history** via chaining.

Third parties can also compare multiple operator-provided bundles; any mismatch is provable.

## Operational Flow

1. **Collect inputs** from authoritative sources.
2. **Canonicalize** and hash each file.
3. **Compute Merkle roots** per artifact type.
4. **Build manifest** with roots and metadata.
5. **Sign manifest** via DSSE + threshold policy.
6. **Publish snapshot bundle** to public storage.
7. **Anchor snapshot hash** to transparency log and OpenTimestamps.

## Security Considerations
- **Key rotation**: each snapshot lists valid signing keys and revocations.
- **Witness diversity**: require signatures from independent organizations.
- **Supply chain integrity**: hardware artifacts must include SBOM + TPM quotes.
- **Anti-replay**: include monotonic `snapshot_id` and `previous_snapshot` link.

## Example Verification Checklist
- Validate `manifest.json` canonical hash.
- Verify Merkle roots for DNS, governance, hardware.
- Verify threshold signatures.
- Verify transparency log inclusion proof.
- Verify OpenTimestamps proof.
- Verify `previous_snapshot` hash continuity.

---

**Result:** The system provides signed, replayable snapshots of DNS, governance, and hardware artifacts, enabling third-party verification without reliance on operator trust.
