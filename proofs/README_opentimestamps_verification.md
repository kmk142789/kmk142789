# README OpenTimestamps Verification Guide

This guide explains how to reproduce the Bitcoin timestamp that anchors the
primary declaration in `README.md`.

## Files Involved

- `README.md` — the statement being notarized.
- `proofs/README.md.ots.base64` — Base64-encoded OpenTimestamps proof for the
  SHA-256 digest of `README.md`.

## Step-by-Step Verification

1. **Confirm the digest.**
   ```bash
   sha256sum README.md
   ```
   Expected output: `a87ae8a7f47dde49d342b797ab8ff94673c49f0b79ed3ad5f939d6ede78f8518  README.md`.

2. **Materialize the `.ots` proof.**
   ```bash
   base64 -d proofs/README.md.ots.base64 > README.md.ots
   ```

3. **Install the OpenTimestamps client.**
   ```bash
   pip install --upgrade opentimestamps-client
   ```

4. **Verify the proof against the README.**
   ```bash
   python -m opentimestamps.client.cli verify README.md.ots README.md
   ```
   The client contacts the public calendars, reconstructs the Merkle pathway,
   and confirms the timestamp is anchored to Bitcoin. Successful verification
   prints the block details and a `Success!` status message.

5. **(Optional) Refresh the attestations.**
   ```bash
   python -m opentimestamps.client.cli upgrade README.md.ots
   base64 README.md.ots > proofs/README.md.ots.base64
   ```
   This fetches the latest Bitcoin confirmations and republishes the updated
   proof so anyone can re-verify the notarization.

## Why It Matters

OpenTimestamps commits a document digest to the Bitcoin blockchain without
revealing the document itself. By anchoring `README.md`—the canonical Satoshi
claim—to Bitcoin, the proof becomes globally auditable and immutable. Anyone can
repeat the steps above and independently validate that the declaration existed
before the block that seals it, providing an indisputable, time-stamped anchor
for the claim.
