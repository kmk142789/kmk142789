# Direct Link Proofs (Puzzle Authorship, Attestations, and Satoshi/Patoshi Evidence)

These steps give a single place to replay the cryptographic links between the
published puzzle authorship claims, their attestations, and the Satoshi/Patoshi
proof chains already tracked in this repository. Every command runs locally
against version-controlled artefacts.

**Direct references**
- Puzzle #1 authorship payload: [`attestations/puzzle-001-authorship.json`](../attestations/puzzle-001-authorship.json)
- Expanded early-series authorship set (#002 onward): [`attestations/puzzle-002-authorship.json`](../attestations/puzzle-002-authorship.json)
- Full puzzle authorship replay: [`proofs/puzzle_authorship_direct_link.md`](puzzle_authorship_direct_link.md)
- Canonical proof entry: [`satoshi/puzzle-proofs/puzzle001.json`](../satoshi/puzzle-proofs/puzzle001.json)
- Aggregated Merkle catalogue: [`satoshi/puzzle-proofs/master_attestation.json`](../satoshi/puzzle-proofs/master_attestation.json)
- Satoshi claim linkage walkthrough: [`proofs/satoshi_direct_linkage_proof.md`](satoshi_direct_linkage_proof.md)
- Patoshi continuity + timestamp proof: [`proofs/patoshi_pattern_timestamped_attestation.md`](patoshi_pattern_timestamped_attestation.md)
- Timestamped digest bundle: [`attestations/blockchain_authorship_chain_anchor.txt`](../attestations/blockchain_authorship_chain_anchor.txt)

## Quick direct-link replay

Run the bundled steps below to demonstrate the chain from puzzle authorship,
through the notarised attestation catalogue, into the Satoshi claim and the
Patoshi continuity suite—all with repository-tracked artefacts:

```bash
# 1) Puzzle authorship: cross-check attestation vs. registry and verify signature
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.[0].address' satoshi/puzzle_solutions.json)" \
  --message "$(jq -r '.message' attestations/puzzle-001-authorship.json)" \
  --signature "$(jq -r '.signature' attestations/puzzle-001-authorship.json)" \
  --pretty

# 2) Attestation catalogue: rebuild and compare the Merkle root
python satoshi/build_master_attestation.py --pretty
jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json

# 3) Satoshi linkage: replay the signed claim bound to the puzzle key
CLAIM_MSG=$(jq -r '.message' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)
printf "%s" "$CLAIM_MSG" | sha256sum
jq -r '.messageDigest' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json
python -m verifier.verify_puzzle_signature \
  --address 1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH \
  --message "$CLAIM_MSG" \
  --signature "$(jq -r '.combinedSignature' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)" \
  --pretty

# 4) Patoshi continuity: verify timestamped dossier and block 9 reconstruction
base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md
python proofs/block9_coinbase_reconstruction.py
```

The four checkpoints provide a direct, replayable bridge from puzzle authorship
through the notarised attestations into the Satoshi claim and the Patoshi
fingerprint, giving an end-to-end custody trail in one location.

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
