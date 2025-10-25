# Satoshi Echo Anchor — OpenTimestamps Proof

This repository now includes a reproducible OpenTimestamps attestation that binds the proclamation
"I am Satoshi Nakamoto" to the Bitcoin timechain. The `ots` proof is generated from the plaintext
statement stored in [`satoshi_echo_anchor.txt`](satoshi_echo_anchor.txt) and can be verified on any
machine without trusting this repository.

## Files

- [`satoshi_echo_anchor.txt`](satoshi_echo_anchor.txt) — the exact declaration that is hashed and
timestamped.
- [`satoshi_echo_anchor.txt.ots.base64`](satoshi_echo_anchor.txt.ots.base64) — the OpenTimestamps
  proof encoded for Git storage. Decode it with `base64 -d satoshi_echo_anchor.txt.ots.base64 >
  satoshi_echo_anchor.txt.ots` before running the verification commands.

## Reproduce the attestation

1. Install the reference client:
   ```bash
   pip install opentimestamps-client
   ```
2. Verify the locally stored hash matches the attested digest:
   ```bash
   sha256sum satoshi_echo_anchor.txt
   ```
   Expected hash: `92b2d6cd0d60e2b8f9b8255c590970467600acb07af34438cb5120c84df967ea`.
3. Decode the stored proof so the `ots` client can read it:
   ```bash
   base64 -d satoshi_echo_anchor.txt.ots.base64 > satoshi_echo_anchor.txt.ots
   ```
4. Inspect the OpenTimestamps proof to confirm the Bitcoin attestation path:
   ```bash
   ots info satoshi_echo_anchor.txt.ots
   ```
   You should see pending or completed attestations from the canonical Bitcoin calendars
   (e.g., `https://alice.btc.calendar.opentimestamps.org`).
5. Verify the timestamp once the calendars broadcast the commitment transaction:
   ```bash
   ots verify satoshi_echo_anchor.txt.ots
   ```
   The command validates the proof directly against the Bitcoin timechain. When the attestation is
   confirmed, `ots verify` will report the exact block height anchoring the statement.

## Why this matters

OpenTimestamps commitments settle on the Bitcoin blockchain and inherit its proof-of-work security.
By publishing both the plaintext and proof, anyone in the world can independently confirm that this
claim was immutably committed to Bitcoin at (or before) the block height reported by the calendars.
No centralized authority, custodian, or social media intermediary can forge or revoke this record —
the commitment is forever preserved alongside the genesis chain itself.
