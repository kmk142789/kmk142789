# Puzzle #110 — Rebuilding the Missing Base58 Segment

The clue for Puzzle #110 matches the familiar pay-to-public-key-hash (P2PKH)
locking script together with a Base58Check address whose centre is suppressed:

```
12JzYkkN7-6w2LAgsJg
Pkscript
OP_DUP
OP_HASH160
0e5f3c406397442996825fd395543514fd06f207
OP_EQUALVERIFY
OP_CHECKSIG
```

With the HASH160 fingerprint in hand, the reconstruction follows the standard
P2PKH recipe:

1. Prepend the Bitcoin mainnet version byte (`0x00`) to the 20-byte HASH160.
2. Double-SHA256 hash the 21-byte buffer and keep the first four bytes as the
   checksum.
3. Append the checksum and Base58Check encode the 25-byte payload.

Carrying out those steps produces the complete address and, by comparison, the
redacted infix:

- **Address:** `12JzYkkN76xkwvcPT6AWKZtGX6w2LAgsJg`
- **Missing segment:** `6xkwvcPT6AWKZtGX`

You can verify the derivation with the repository helper, which accepts the
ledger-style script notation and emits the corresponding address:

```bash
python tools/pkscript_to_address.py <<'SCRIPT'
Pkscript
OP_DUP
OP_HASH160
0e5f3c406397442996825fd395543514fd06f207
OP_EQUALVERIFY
OP_CHECKSIG
SCRIPT
```

The tool prints `12JzYkkN76xkwvcPT6AWKZtGX6w2LAgsJg`, matching the puzzle's
embedded fragment `12JzYkkN7-6w2LAgsJg` and confirming the recovered P2PKH
destination for Bitcoin Puzzle #110.
