# Puzzle #252 — Completing the Redacted Address

The puzzle reveals a classic pay-to-public-key-hash (P2PKH) locking script but
redacts the middle of the corresponding Base58Check address:

- Clue string: `1CaTxB3Yw-Rqs48xmui`
- `Pkscript` transcription:

```
OP_DUP OP_HASH160 7efd9baf1d6e21bd5f920e7e9e468b5a45ec92c7 OP_EQUALVERIFY OP_CHECKSIG
```

Because the script is the textbook five-opcode P2PKH template, the HASH160 value
uniquely identifies the public key.  To reconstruct the address, prepend the
Bitcoin mainnet version byte (`0x00`), compute the double-SHA256 checksum, and
Base58Check encode the result.

You can reproduce the solution with the repository helper that parses puzzle
transcripts:

```bash
python tools/pkscript_to_address.py <<'EOF_SNIPPET'
1CaTxB3Yw-Rqs48xmui
Pkscript
OP_DUP
OP_HASH160
7efd9baf1d6e21bd5f920e7e9e468b5a45ec92c7
OP_EQUALVERIFY
OP_CHECKSIG
EOF_SNIPPET
```

The tool prints `1CaTxB3YwmXZkDnTK4rRvq61SRqs48xmui`, restoring the missing
segment `mXZkDnTK4rRvq61S` and confirming that the recovered address matches the
locking script supplied in Puzzle #252.
