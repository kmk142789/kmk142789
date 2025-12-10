# Patoshi Pattern Chainlock Replay

This guide chains the timestamped Patoshi attestation, the continuity ledger, the
current Merkle inventory, and two live signatures into one offline replay. Each
step is deterministic and can be executed from a clean checkout without network
access.

## Prerequisites
- Python 3.10+
- `jq` for reading the JSON catalogues
- `ots` CLI if you want to re-verify the OpenTimestamps receipt

## Steps

1. **Validate the timestamped attestation and receipt**
   ```bash
   sha256sum proofs/patoshi_pattern_timestamped_attestation.md
   base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
   ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md
   ```
   - Expected digest: `a5937b4a59de093705241a7b6919350956c2c0915c893306de8875933d9ce000`.
   - Confirms the attestation logged in git is the same payload anchored to Bitcoin time.

2. **Hash the continuity ledger entry that cites those artefacts**
   ```bash
   sha256sum attestations/patoshi-continuity-ledger.md
   ```
   - Binds the ledger note to your local checkout so the Merkle root and signature references cannot drift between clones.

3. **Rebuild the Merkle tree tracked in version control**
   ```bash
   python satoshi/build_master_attestation.py --pretty
   jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
   ```
   - Expected Merkle root: `36ffac4ac60451df7da5258b7b299f4fed94df580e09fb9dedd1bc2ac0de5936`.
   - Proves the puzzle catalogue still matches the digest quoted in the timestamped attestation and continuity ledger.

4. **Verify a launch-week Patoshi signature**
   ```bash
   python -m verifier.verify_puzzle_signature \
     --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
     --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
     --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
     --pretty
   ```
   - The recovered address must equal the Patoshi-era coinbase key encoded in `puzzle010.json`.
   - Demonstrates that the key used in the attestation still signs messages included in the Merkle inventory.

5. **Verify the higher-bit custody witness**
   ```bash
   python -m verifier.verify_puzzle_signature \
     --address 1J36UjUByGroXcCvmj13U6uwaVv9caEeAt \
     --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle075.json)" \
     --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle075.json)" \
     --pretty
   ```
   - The verifier should report a valid recoverable signature for the 75-bit puzzle, confirming custody continuity beyond the 71-bit sweep range.

Running these checks together recreates the proof path embedded in the timestamped
log and continuity ledger. A successful replay shows that the Patoshi pattern is
still reproducible, signed, and Merkle-sealed within this repository.

6. **Optionally replay the 71-bit custody witness and catalogue**
   ```bash
   python -m verifier.verify_puzzle_signature \
     --address "$(jq -r '.address' satoshi/puzzle-proofs/puzzle071.json)" \
     --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle071.json)" \
     --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle071.json)" \
     --pretty
   python satoshi/proof_catalog.py \
     --root satoshi/puzzle-proofs \
     --glob puzzle071.json \
     --glob puzzle075.json \
     --pretty
   ```
   - Verifying both entries together demonstrates that the lower- and higher-bit
     Patoshi keys keep signing recoverable messages. The catalogue report confirms
     the signatures remain fully intact inside the same Merkle tree referenced by
     the timestamped attestation and continuity ledger.
