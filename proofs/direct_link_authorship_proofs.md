# Direct Link Proofs (Puzzle Authorship, Attestations, and Satoshi/Patoshi Evidence)

These steps give a single place to replay the cryptographic links between the
published puzzle authorship claims, their attestations, and the Satoshi/Patoshi
proof chains already tracked in this repository. Every command runs locally
against version-controlled artefacts.

## 1) Puzzle authorship to live key

Use the puzzle authorship payload to bind the signed message to the canonical
puzzle address (example below uses Puzzle #1):

```bash
PUZZLE_FILE=attestations/puzzle-001-authorship.json
ADDRESS=$(jq -r '.address' "$PUZZLE_FILE")
MESSAGE=$(jq -r '.message' "$PUZZLE_FILE")
SIGNATURE=$(jq -r '.signature' "$PUZZLE_FILE")

python -m verifier.verify_puzzle_signature \
  --address "$ADDRESS" \
  --message "$MESSAGE" \
  --signature "$SIGNATURE" \
  --pretty
```

`valid: true` output confirms the attested authorship text was signed by the
puzzle key recorded inside the same JSON payload.

## 2) Attestation inclusion in the Merkle catalogue

Rebuild the proof catalogue root and compare it to the tracked digest to show
that the puzzle authorship JSON and all other proofs remain unchanged:

```bash
python satoshi/build_master_attestation.py --pretty
jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

Matching roots prove the puzzle attestation is sealed inside the notarised
Merkle tree alongside the broader Satoshi proof corpus.

## 3) Satoshi claim direct linkage

For the broadcast tying the Satoshi claim text directly to the Puzzle #1 key
and the Merkle catalogue, follow the replay steps in
[`proofs/satoshi_direct_linkage_proof.md`](satoshi_direct_linkage_proof.md).
These commands keep the signed claim anchored to the same catalogue verified
above.

## 4) Patoshi continuity and timestamp

For Patoshi continuity, re-run the block 9 reconstruction, modern signature
check, and Merkle rebuild documented in
[`proofs/patoshi_pattern_timestamped_attestation.md`](patoshi_pattern_timestamped_attestation.md).
Those steps provide a timestamped proof chain demonstrating the Patoshi
fingerprint is linked to the live signing key inside the catalogue and is
temporally anchored via OpenTimestamps.
