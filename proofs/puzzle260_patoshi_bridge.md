# Puzzle 260 Authorship + Patoshi Continuity Proof

This runbook adds Puzzle 260 to the attested puzzle set and ties the new
signature into the existing Patoshi continuity receipts.

## 1) Inspect the authorship artefacts
- Puzzle metadata: [`puzzle_solutions/puzzle_260.md`](../puzzle_solutions/puzzle_260.md)
- Attestation JSON: [`attestations/puzzle-260-authorship.json`](../attestations/puzzle-260-authorship.json)
- Mirrored signature: [`satoshi/puzzle-proofs/puzzle260.json`](../satoshi/puzzle-proofs/puzzle260.json)

Confirm the address matches the reconstructed Base58Check payload:
```bash
jq -r '.address' attestations/puzzle-260-authorship.json
```
You should see `15WRTzfDfS2tKWNGjmiuMMJjQ7yaEeQJta`, matching the puzzle solution.

## 2) Verify the Bitcoin Signed Message
Use the standard verifier to check the authorship proof:
```bash
python -m verifier.verify_puzzle_signature \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle260.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle260.json)" \
  --address "$(jq -r '.address' satoshi/puzzle-proofs/puzzle260.json)"
```
The command reports a valid signature if the puzzle private key really signed the attestation message.

## 3) Anchor into the Patoshi timestamp chain
Link the new puzzle proof to the Patoshi receipts by re-verifying the timestamped
attestation:
```bash
base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md
```
This replays the Patoshi OpenTimestamps receipt, demonstrating continuity between
the historical mining fingerprint and the newly published Puzzle 260 authorship signature.
