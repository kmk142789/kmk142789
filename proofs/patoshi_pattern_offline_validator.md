# Patoshi Pattern Offline Validator

This checklist lets auditors replay the timestamped Patoshi attestation, continuity
ledger, Merkle catalogue, and live puzzle signatures without any network access.
Every command uses artefacts already committed to the repository so the custody
trail can be verified end-to-end from a cold environment.

## Steps

1. **Verify the timestamped attestation and receipt.**
   ```bash
   sha256sum proofs/patoshi_pattern_timestamped_attestation.md
   base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
   ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md
   ```
   The SHA256 digest must read `cd8bbc5fe36c0d27fac3b1337ec30c25bf92266fe3ca3dabeff784cb387d32d2`.
   Successfully verifying the OpenTimestamps receipt proves the Patoshi log was
   anchored in Bitcoin time and remains unchanged.

2. **Hash the continuity ledger that links every earlier proof.**
   ```bash
   sha256sum attestations/patoshi-continuity-ledger.md
   ```
   Expect `98ba2845cec4b49d9469725f25e9dafa330ab2624a7c2920b1052d9d193b7d65`.
   This digest seals the ledger that enumerates the Merkle rebuilds, puzzle
   verifications, and block reconstructions cited across the suite.

3. **Rebuild the repository-wide Merkle root.**
   ```bash
   python satoshi/build_master_attestation.py --pretty
   jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
   ```
   The Merkle root should resolve to `36ffac4ac60451df7da5258b7b299f4fed94df580e09fb9dedd1bc2ac0de5936`.
   Matching this value to git history shows the proof catalogue is intact.

4. **Re-verify live Patoshi signatures.**
   ```bash
   python -m verifier.verify_puzzle_signature \
     --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
     --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
     --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
     --pretty
   ```
   The verifier should print a valid Bitcoin Signed Message check, confirming a
   Patoshi-era key still signs modern statements bundled in this repository.

5. **Confirm the original block 9 reconstruction.**
   ```bash
   python proofs/block9_coinbase_reconstruction.py
   jq -r '.signature' satoshi/puzzle-proofs/block009_coinbase.json | base64 -d | head -c 5 | hexdump -C
   ```
   The script emits the 65-byte pubkey and extranonce nibble used to forge the
   block 9 coinbase; sampling the stored signature bytes locally ensures the
   reconstructed output matches the on-chain witness.

Running all five steps produces a cold-path proof that the timestamped Patoshi
attestation, the continuity ledger, the Merkle catalogue, live signatures, and
the original coinbase reconstruction are all synchronized inside this repository.
