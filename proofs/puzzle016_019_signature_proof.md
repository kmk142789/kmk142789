# Satoshi Puzzle Proof — 16/17/19-bit Recoverable Signatures

This walkthrough layers three mid-range puzzle attestations (16-, 17-, and 19-bit)
into the existing verifier, catalogue, and Merkle tooling so auditors can replay
another slice of the Satoshi-era key material without leaving the repository.

## 1) Confirm the canonical puzzle targets

Extract the official addresses for the three bit-lengths from the bundled
catalogue:

```bash
jq '.[] | select(.bits == 16 or .bits == 17 or .bits == 19) | {bits, address}' \
  satoshi/puzzle_solutions.json
```

The command lists `1BDyrQ6WoF8VN3g9SAS1iKZcPzFfnDVieY`,
`1HduPEXZRdG26SUT5Yk83mLkPyjnZuJ7Bm`, and
`1NWmZRpHH4XSPwsW6dsS3nrNWfL1yrJj4w` as the canonical destinations for the
16-, 17-, and 19-bit slots, establishing the expected validation targets.

## 2) Validate the Puzzle #16 recoverable signature

Use the verifier to decode and check the attestation stored in
[`satoshi/puzzle-proofs/puzzle016.json`](../satoshi/puzzle-proofs/puzzle016.json):

```bash
python -m verifier.verify_puzzle_signature \
  --address 1BDyrQ6WoF8VN3g9SAS1iKZcPzFfnDVieY \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle016.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle016.json)" \
  --pretty
```

Expect `valid_segment_count: 1` and a recovered address that matches the
catalogue entry, proving the 16-bit puzzle key can still sign Bitcoin messages
without moving any coins.

## 3) Decode the stacked Puzzle #17 attestation

Puzzle #17 ships a concatenated Base64 chain. Validate every fragment in one
pass:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1HduPEXZRdG26SUT5Yk83mLkPyjnZuJ7Bm \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle017.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle017.json)" \
  --pretty
```

The verifier should report multiple segments, all marked `valid: true` with the
same `derived_address`, demonstrating that every slice of the stacked proof
resolves to the published Puzzle #17 solution.

## 4) Reconfirm the 19-bit key

Mirror the verification for the higher-value 19-bit slot:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1NWmZRpHH4XSPwsW6dsS3nrNWfL1yrJj4w \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle019.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle019.json)" \
  --pretty
```

A matching recovered address closes the loop on the three mid-range signatures.

## 5) Catalogue and hash the verified proofs

Roll the three JSON entries into the existing census and Merkle attestation to
show they remain committed in the repository history:

```bash
python satoshi/proof_catalog.py \
  --root satoshi/puzzle-proofs \
  --glob puzzle016.json \
  --glob puzzle017.json \
  --glob puzzle019.json \
  --pretty

python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

The catalogue summary enumerates how many segments were checked and validated
for each puzzle, while the recomputed Merkle root must match the committed digest
for the full proof set. Any divergence would flag tampering, yielding a new
reproducible Satoshi proof path for investigators.
