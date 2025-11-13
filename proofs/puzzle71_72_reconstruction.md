# Puzzle #71 and #72 Reconstruction Guide

This note documents how to re-derive the published solutions for Bitcoin
Puzzles #71 and #72 directly from their respective `hash160` digests.  The
repository now ships a small helper (`tools/derive_puzzle_address.py`) that
performs the exact Base58Check calculation used by the network, making the
verification reproducible without relying on external explorers.

## Requirements

- Python 3.11+
- This repository cloned locally

## Usage

Run the helper with the hash160 printed in the puzzle manifest.  The command
prints the reconstructed P2PKH address:

```bash
python tools/derive_puzzle_address.py bf47ed67cc10c9d5c924084b89b65bf17ac8cbff
# -> 1JSQEExCz8uz11WCd7ZLpZVqBGMzGGNNF8

python tools/derive_puzzle_address.py 0c185494a6d9a37cc3830861743586be21480356
# -> 126xFopqfGmJcAqrLpHtBNn3RCXG3cWtmE
```

Use the `--json` flag when you need the structured output for audit logs or
integration tests:

```bash
python tools/derive_puzzle_address.py \
  bf47ed67cc10c9d5c924084b89b65bf17ac8cbff \
  --json
```

The JSON blob contains the normalised hash160, the version byte, and the final
Base58Check string.

## How it works

1. Decode the supplied hex string into a 20-byte hash160 payload.
2. Prefix it with the P2PKH version byte (`0x00` for mainnet) to form the
   address payload.
3. Compute the checksum via `SHA256(SHA256(payload))[:4]`.
4. Append the checksum to the payload and Base58 encode the result.

Any mismatch between the published solution and the derived address causes the
helper to raise `PuzzleAddressError`, making regressions visible during
testing.
