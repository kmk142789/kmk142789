# Puzzle #180 Solution

- **Locking script**: `OP_DUP OP_HASH160 a02a21260cc2297a22a798bb8e4a5efd1745ee91 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `a02a21260cc2297a22a798bb8e4a5efd1745ee91`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 a0 2a 21 26 0c c2 29 7a 22 a7 98 bb 8e 4a 5e fd 17 45 ee 91`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `2d 06 8e 40`
- **Base58Check encoding**: `1FbsauFjMP9E3fzcSYSenPHNNyARwgRp6K`

Therefore, the completed Bitcoin address for the given locking script is:

```
1FbsauFjMP9E3fzcSYSenPHNNyARwgRp6K
```
