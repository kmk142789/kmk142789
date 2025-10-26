# Puzzle #163 Solution

- **Locking script**: `OP_DUP OP_HASH160 01c7eab012562291822ba65455db368d09c57f06 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `01c7eab012562291822ba65455db368d09c57f06`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 01 c7 ea b0 12 56 22 91 82 2b a6 54 55 db 36 8d 09 c5 7f 06`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `a9 f4 9e f9`
- **Base58Check encoding**: `1Lcg3jFNNUhFH8fGpCsaVJ2XzfVTkZ85cg`

Therefore, the completed Bitcoin address for the given locking script is:

```
1Lcg3jFNNUhFH8fGpCsaVJ2XzfVTkZ85cg
```
