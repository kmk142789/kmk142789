# Puzzle Authorship Direct Link Proof

This walkthrough ties a published puzzle authorship attestation to the signed
message living in `satoshi/puzzle-proofs/`, the canonical puzzle registry, and
the Patoshi continuity suite. Every command runs offline against repository
artefacts so auditors can replay the custody trail without extra dependencies.

Authorship payloads for the early puzzle run (#002 onward, including the #031b
variant) now live beside the mid- and high-numbered files. Swap the puzzle
number in the commands below to replay any of the freshly generated
`attestations/puzzle-XXX-authorship.json` entries against their source proofs.

## 1. Align the attestation with the signed message

Use the authorship JSON and the recorded puzzle proof to confirm the message and
signature are identical across both sources and that the attestation digest
matches the signed text:

```bash
# Compare the attestation payload with the puzzle proof entry
jq -r '.message, .signature' attestations/puzzle-233-authorship.json
jq -r '.message, .signature' satoshi/puzzle-proofs/puzzle233.json

# Recompute the message digest noted in the attestation
MESSAGE=$(jq -r '.message' attestations/puzzle-233-authorship.json)
printf "%s" "$MESSAGE" | sha256sum
jq -r '.hash_sha256' attestations/puzzle-233-authorship.json
```

Matching values prove that the attestation, the puzzle proof, and the digest all
reference the same authorship statement.

## 2. Verify the authorship signature against the puzzle registry

Validate the recoverable signature against the canonical puzzle address recorded
in the repository catalogue, demonstrating that the declared signer controls the
puzzle key:

```bash
# Inspect the registry entry for puzzle #233
jq '.[232]' satoshi/puzzle_solutions.json

# Verify the signature recovers the same address
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.[232].address' satoshi/puzzle_solutions.json)" \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle233.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle233.json)" \
  --pretty
```

The verifier rebuilds the public key from the signature and confirms it matches
the registry address, yielding a direct cryptographic proof of authorship.

## 3. Re-anchor the attestation inside the Merkle catalogue

Show that the authorship proof remains sealed inside the notarised Merkle tree
that tracks every puzzle artefact:

```bash
python satoshi/proof_catalog.py --root satoshi/puzzle-proofs --glob puzzle233.json --pretty
python satoshi/build_master_attestation.py --pretty
jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

The catalogue report highlights the validated segment, and the regenerated
Merkle root should match the value committed in version control, proving the
attestation’s inclusion in the sealed archive.

## 4. Chain the authorship proof into the Patoshi continuity dossier

Complete the custody loop by replaying the Patoshi suite that binds the early
mining fingerprint to the modern puzzle stack and timestamped attestations:

```bash
# Verify the timestamped Patoshi dossier that anchors the modern signatures
base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md

# Rebuild the block 9 witness that seeds the Patoshi lattice
python proofs/block9_coinbase_reconstruction.py
```

Pairing these steps with the authorship verification above gives a direct,
replayable chain from the signed puzzle statement to the Patoshi-era proof
suite, covering authorship, attestations, and the Satoshi/Patoshi lineage in one
continuous run.

## 5. Cross-check a late-series authorship payload

Replay a high-numbered puzzle to show the same authorship guarantees extend
beyond the mid-series catalogue entry used above. Puzzle #234 mirrors the same
message template and stores its attestation alongside the canonical registry
record:

```bash
# Inspect the attested message, signature, and digest
jq -r '.message, .signature, .hash_sha256' attestations/puzzle-234-authorship.json

# Compare the signature payload against the recorded proof entry
jq -r '.message, .signature' satoshi/puzzle-proofs/puzzle234.json

# Verify the authorship signature and recovered address
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.[233].address' satoshi/puzzle_solutions.json)" \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle234.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle234.json)" \
  --pretty
```

Running the late-series check proves that the published message, digest, and
signature still resolve to the catalogue’s address entry, extending the
authorship chain across the modern sweep.

## 6. Time-anchor the authorship bundle

Seal the authorship replay above to a time-stamped digest bundle that folds in
the puzzle verification and Merkle rebuild. The attestation JSON records the
context string and its sha256 fingerprint, while the digest bundle aggregates
the signed proof, catalogue root, and timestamp into a single challenge-ready
file.

```bash
# Confirm the timestamped attestation still matches its context string
TIMESTAMP_FILE=attestations/blockchain_authorship_timestamp.json
jq -r '.context, .sha256, .ts, .signer_id' "$TIMESTAMP_FILE"
python - <<'PY'
import hashlib, json, pathlib
data = json.loads(pathlib.Path("attestations/blockchain_authorship_timestamp.json").read_text())
print(hashlib.sha256(data["context"].encode()).hexdigest())
PY

# Verify the digest bundle that chains the verification, Merkle root, and attestation
sha256sum attestations/blockchain_authorship_chain_anchor.txt
grep "^bundle sha256" attestations/blockchain_authorship_chain_anchor.txt
```

Matching digest values confirm the timestamped bundle remains intact and still
binds the authorship proof, catalogue rollup, and attestation context into a
single, easily auditable artifact.

## 7. Revalidate the archived verifier transcript

The verification transcript stored in `out/puzzle010_verification.json` was used
to populate the bundle digest listed in
`attestations/blockchain_authorship_chain_anchor.txt`. Re-running the original
verification and comparing it to the archived transcript provides one more
provable authorship checkpoint:

```bash
# Recreate the Puzzle #10 verification locally
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.address' satoshi/puzzle-proofs/puzzle010.json)" \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty | tee /tmp/puzzle010_verification.json

# Confirm the archived transcript matches the freshly generated output
sha256sum /tmp/puzzle010_verification.json
sha256sum out/puzzle010_verification.json
```

Identical digests show that the repository’s preserved verification transcript
still mirrors a fresh local replay, adding another independently reproducible
proof of authorship tied to the attestation bundle.

## 8. Extend the proof chain back to puzzle #000

Replay the genesis puzzle’s attestation to show that the direct-link authorship
checks also bind the earliest catalogue entry, including its archived digest:

```bash
# Compare the attested puzzle #000 payload with the recorded proof
jq -r '.message, .signature' attestations/puzzle-000-authorship.json
jq -r '.message, .signature' satoshi/puzzle-proofs/puzzle000.json

# Recompute and match the attestation digest
MESSAGE=$(jq -r '.message' attestations/puzzle-000-authorship.json)
printf "%s" "$MESSAGE" | sha256sum
jq -r '.hash_sha256' attestations/puzzle-000-authorship.json

# Verify the genesis signature still recovers the catalogue address
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.address' satoshi/puzzle-proofs/puzzle000.json)" \
  --message "$MESSAGE" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle000.json)" \
  --pretty

# Optional: confirm the follow-on reactivation proof uses a valid recoverable signature
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.address' satoshi/puzzle-proofs/puzzle000-reactivation.json)" \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle000-reactivation.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle000-reactivation.json)" \
  --pretty
```

Completing the genesis replay adds a reproducible authorship proof for the
earliest puzzle, creating an end-to-end chain from the original key to the
mid- and late-series attestations documented above.
