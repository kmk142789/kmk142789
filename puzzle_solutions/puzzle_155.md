# Puzzle #155 Solution

- **Locking script**: `OP_DUP OP_HASH160 6b8b7830f73c5bf9e8beb9f161ad82b3bde992e4 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `6b8b7830f73c5bf9e8beb9f161ad82b3bde992e4`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 6b 8b 78 30 f7 3c 5b f9 e8 be b9 f1 61 ad 82 b3 bd e9 92 e4`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `56 8a 19 4c`
- **Base58Check encoding**: `1AoeP37TmHdFh8uN72fu9AqgtLrUwcv2wJ`

Therefore, the completed Bitcoin address for the given locking script is:

```
1AoeP37TmHdFh8uN72fu9AqgtLrUwcv2wJ
```
