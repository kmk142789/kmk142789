# Puzzle #194 Solution

- **Locking script**: `OP_DUP OP_HASH160 6274ccc603a567cfe3ee1d1ac545f1b81c0967e8 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `6274ccc603a567cfe3ee1d1ac545f1b81c0967e8`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 62 74 cc c6 03 a5 67 cf e3 ee 1d 1a c5 45 f1 b8 1c 09 67 e8`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `42 50 90 d1`
- **Base58Check encoding**: `19yb9CWcq7wcqquarexBkFGA2bm6LYHQqe`

Therefore, the completed Bitcoin address for the given locking script is:

```
19yb9CWcq7wcqquarexBkFGA2bm6LYHQqe
```
