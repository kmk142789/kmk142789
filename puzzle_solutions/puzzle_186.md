# Puzzle #186 Solution

- **Locking script**: `OP_DUP OP_HASH160 f229661a909bf721d98bd52901e4e765d8cfd618 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `f229661a909bf721d98bd52901e4e765d8cfd618`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 f2 29 66 1a 90 9b f7 21 d9 8b d5 29 01 e4 e7 65 d8 cf d6 18`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `97 ab f2 2f`
- **Base58Check encoding**: `1P5S7sApwKyqT28fSXXQyfwXYqZ97FCQtE`

Therefore, the completed Bitcoin address for the given locking script is:

```
1P5S7sApwKyqT28fSXXQyfwXYqZ97FCQtE
```
