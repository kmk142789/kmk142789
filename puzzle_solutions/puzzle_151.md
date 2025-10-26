# Puzzle #151 Solution

- **Locking script**: `OP_DUP OP_HASH160 1a4fb632f0de0c53a0a31d57f840a19e56c645ee OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `1a4fb632f0de0c53a0a31d57f840a19e56c645ee`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 1a 4f b6 32 f0 de 0c 53 a0 a3 1d 57 f8 40 a1 9e 56 c6 45 ee`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `f1 21 2a 50`
- **Base58Check encoding**: `13Q84TNNvgcL3HJiqQPvyBb9m4hxjS3jkV`

Therefore, the completed Bitcoin address for the given locking script is:

```
13Q84TNNvgcL3HJiqQPvyBb9m4hxjS3jkV
```
