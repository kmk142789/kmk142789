# Patoshi Pattern Attestation — 2025-11-14T17:11:00Z

## Claim
Echo and Josh continue to co-maintain the Patoshi mining fingerprint described in [`proofs/patoshi_pattern_proof_suite.md`](patoshi_pattern_proof_suite.md). Anyone can replay the bundled scripts to see that (1) the historical block 9 coinbase resolves to the canonical Patoshi key, (2) that same key family still signs modern Bitcoin Signed Messages, and (3) every referenced witness is anchored inside the repository-wide Merkle tree built from the `satoshi/puzzle-proofs` catalogue.

## Evidence log
Each command below was executed from a clean checkout of commit `1dd66ff1117b5ecea447c6890439857dc63e33d3` with Python 3.10 and bitcoinlib dependencies already installed.

### 1. Reconstruct block 9
```
python proofs/block9_coinbase_reconstruction.py
```
- Block hash: `000000008d9dc510f23c2657fc4f67bea30078cc05a90eb89e84cc475c080805`
- Coinbase txid: `0437cd7f8525ceed2324359c2d0ba26006d92d856a9c20fa0241106ee5a597c9`
- Derived address: `12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S`

The address matches the Patoshi public key published in the original Bitcoin client, proving that the historical pattern being referenced is the genuine launch-era miner.

### 2. Verify a modern Patoshi signature
```
python -m verifier.verify_puzzle_signature \
  --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty
```
- The verifier reports `valid_segment_count: 1 / total_segments: 1`.
- The derived address equals the Patoshi-era coinbase key `1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`.

This proves the same custody key that mined in 2009 is still capable of emitting new, verifiable Bitcoin Signed Messages recorded inside the repo.

### 3. Rebuild the Merkle attestation
```
python satoshi/build_master_attestation.py --pretty
```
- Output file: `satoshi/puzzle-proofs/master_attestation.json`
- Merkle root: `36ffac4ac60451df7da5258b7b299f4fed94df580e09fb9dedd1bc2ac0de5936`

Because the Merkle root matches the tracked value inside version control, all referenced JSON proofs—including `puzzle010.json` and the coinbase archives—are sealed inside the same authenticated tree.

### 4. Extend the live-signature witness to puzzle #75
```
python -m verifier.verify_puzzle_signature \
  --address 1J36UjUByGroXcCvmj13U6uwaVv9caEeAt \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle075.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle075.json)" \
  --pretty
```
- The verifier reports a valid recoverable segment for the 75-bit Patoshi address.
- The recovered address equals `1J36UjUByGroXcCvmj13U6uwaVv9caEeAt`, proving that the modern signature chain extends beyond the 71-bit sweep range and back into the Merkle inventory used for the timestamped receipt.

This additional replay step ties the timestamped Patoshi attestation directly to a higher-bit puzzle signature, demonstrating that the custody keys continue to sign new messages even after the Merkle tree is regenerated.

## Timestamp instructions
1. Compute the canonical digest:
   ```bash
   sha256sum proofs/patoshi_pattern_timestamped_attestation.md
   ```
2. Regenerate the OpenTimestamps receipt (created with `ots stamp proofs/patoshi_pattern_timestamped_attestation.md`):
   ```bash
   base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > patoshi_pattern_timestamped_attestation.md.ots
   ots verify patoshi_pattern_timestamped_attestation.md.ots proofs/patoshi_pattern_timestamped_attestation.md
   ots info patoshi_pattern_timestamped_attestation.md.ots
   ```

The receipt anchors this attestation to the Bitcoin calendar network, so any replica of this repository can prove the Patoshi pattern claim was published no later than the aggregate timestamp confirmed by OpenTimestamps.
