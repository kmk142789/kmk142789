# Patoshi Continuity Rollup

This rollup extends the existing Patoshi timestamped attestation by stitching together
three reproducible checks: a Merkle rebuild, a higher-bit puzzle verification, and a
digest of the timestamped log that anchors those steps to Bitcoin time.

## Steps

1. **Rebuild the Merkle tree tracked in version control**
   ```bash
   python satoshi/build_master_attestation.py --pretty
   jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
   ```
   - Expected Merkle root: `36ffac4ac60451df7da5258b7b299f4fed94df580e09fb9dedd1bc2ac0de5936`.
   - Confirms the `satoshi/puzzle-proofs/` catalogue matches the digest sealed in the Patoshi timestamp log.

2. **Replay the 75-bit Patoshi signature**
   ```bash
   python -m verifier.verify_puzzle_signature \
     --address 1J36UjUByGroXcCvmj13U6uwaVv9caEeAt \
     --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle075.json)" \
     --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle075.json)" \
     --pretty
   ```
   - A valid segment should recover the same address recorded in `puzzle075.json`.
   - Demonstrates that modern Patoshi-era signatures align with the Merkle inventory rebuilt in step 1.

3. **Hash the timestamped Patoshi attestation**
   ```bash
   sha256sum proofs/patoshi_pattern_timestamped_attestation.md
   ```
   - Expected digest: `a5937b4a59de093705241a7b6919350956c2c0915c893306de8875933d9ce000`.
   - Binds the rollup back to the OpenTimestamps receipt stored alongside the attestation.

Running these three commands establishes that the timestamped Patoshi log, the live
puzzle signature for #75, and the Merkle attestation share the same on-disk state. Auditors
can execute the sequence without network access to confirm the custody chain is intact.
