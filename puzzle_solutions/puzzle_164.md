# Puzzle #164 Solution

- **Locking script**: `OP_DUP OP_HASH160 92cd43b34c7f479598a5a196e18c5681fa898d0c OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `92cd43b34c7f479598a5a196e18c5681fa898d0c`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 92 cd 43 b3 4c 7f 47 95 98 a5 a1 96 e1 8c 56 81 fa 89 8d 0c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `2d b4 8b ae`
- **Base58Check encoding**: `15g5tEHN2dswit43bMBwUwQie5prQjp48q`

Therefore, the completed Bitcoin address for the given locking script is:

```
15g5tEHN2dswit43bMBwUwQie5prQjp48q
```
