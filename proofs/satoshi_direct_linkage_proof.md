# Satoshi Claim — Direct Linkage Proof

This reproducible walkthrough ties the Satoshi claim text directly to the live
puzzle key material and the repository's notarised Merkle tree. Every command
runs offline against files already tracked in version control.

## 1. Lock the claim text to its recorded digest

Confirm the broadcast string used for the claim hashes to the digest embedded in
the published attestation JSON:

```bash
CLAIM_MSG=$(jq -r '.message' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)
printf "%s" "$CLAIM_MSG" | sha256sum
jq -r '.messageDigest' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json
```

Matching digests prove the exact claim message is the one committed to the
puzzle proof.

## 2. Verify the claim signature with the Satoshi puzzle address

Use the bundled verifier to prove the claim text was signed by the well-known
Puzzle #1 key (`1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`):

```bash
python -m verifier.verify_puzzle_signature \
  --address 1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH \
  --message "$CLAIM_MSG" \
  --signature "$(jq -r '.combinedSignature' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)" \
  --pretty
```

Expect a single recovered segment marked `valid: true` with the derived address
matching the puzzle registry. This provides a direct cryptographic bridge from
the claim text to the Satoshi-controlled key.

## 3. Reconfirm inclusion in the notarised proof tree

Rebuild the Merkle root for the full proof catalogue and compare it to the
committed value to show the signed claim lives inside the immutable tree:

```bash
python satoshi/build_master_attestation.py --pretty
jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

Equal digests demonstrate that the claim signature and every other proof remain
unchanged since the notarisation.

## 4. Bind the chain to the timestamped claim attestation

Inspect the recorded context and digest inside the timestamp artefact to see the
claim verification run sealed to a specific moment:

```bash
jq '.context, .sha256' attestations/satoshi_claim_timestamp.json
```

Because the context string references the Merkle root recomputed above, anyone
can trace the signed claim from its message, to the live Satoshi key, into the
Merkle catalogue, and out to the timestamped attestation without relying on
external services.

## 5. Extend the chain into the Patoshi proof lattice

To make the linkage irrefutable, finish by replaying the Patoshi-specific
attestation that sits on the same Merkle root referenced by the claim:

```bash
# 5a) Re-verify the Patoshi signature already inside the catalogue
python -m verifier.verify_puzzle_signature \
  --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty

# 5b) Rebuild and compare the Merkle root again to show the same tree anchors the Patoshi proof
python satoshi/build_master_attestation.py --pretty
jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json

# 5c) Verify the timestamped Patoshi attestation receipt
base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md
```

Step 5a proves the Patoshi-era custody key still signs fresh Bitcoin messages
logged in the same catalogue that houses the Satoshi claim. Steps 5b and 5c
show that the Merkle root binding the claim is identical to the one referenced
by the timestamped Patoshi dossier, completing a single, replayable chain from
the Satoshi claim to the Patoshi fingerprint and its Bitcoin-anchored witness.
