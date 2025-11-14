# Bitcoin Puzzle #253 — Restoring the Base58 Middle Segment

Puzzle #253 publishes the textbook pay-to-public-key-hash (P2PKH) locking
script together with a Base58Check address whose middle section was redacted:

- Clue string: `1JqRqUPHH-2jbZxEqFj`
- Pkscript transcription:

```
OP_DUP
OP_HASH160
c3a2d618736baf0d5df7d81d5b8235cf8a266448
OP_EQUALVERIFY
OP_CHECKSIG
```

Because the opcode pattern is the canonical five-opcode P2PKH template, the
HASH160 fingerprint uniquely determines the public key. Recreating the missing
characters only requires re-running the standard Base58Check encoding steps:

1. Prefix the 20-byte HASH160 digest with the Bitcoin mainnet version byte
   (`0x00`).
2. Double-SHA256 the 21-byte payload and keep the first four checksum bytes.
3. Append the checksum to the payload and encode the 25-byte buffer with the
   Bitcoin Base58 alphabet.

Running the helper that decodes puzzle transcripts reproduces the completed
address:

```bash
python tools/pkscript_to_address.py <<'EOF_SNIPPET'
1JqRqUPHH-2jbZxEqFj
Pkscript
OP_DUP
OP_HASH160
c3a2d618736baf0d5df7d81d5b8235cf8a266448
OP_EQUALVERIFY
OP_CHECKSIG
EOF_SNIPPET
```

The tool prints `1JqRqUPHHcQu2yrr8JZzxSYDx2jbZxEqFj`, restoring the removed
segment `cQu2yrr8JZzxSYDx` and confirming the expected legacy P2PKH output for
Bitcoin Puzzle #253.
