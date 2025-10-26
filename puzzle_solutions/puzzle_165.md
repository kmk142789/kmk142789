# Puzzle #165 Solution

- **Locking script**: `OP_DUP OP_HASH160 c20cfe57ce411e2bc88f5173578f22930e330de2 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `c20cfe57ce411e2bc88f5173578f22930e330de2`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 c2 0c fe 57 ce 41 1e 2b c8 8f 51 73 57 8f 22 93 0e 33 0d e2`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `21 c0 fb cd`
- **Base58Check encoding**: `15i6LxQazwqKcQzUcxRoTojoFiTDqi1j2X`

Therefore, the completed Bitcoin address for the given locking script is:

```
15i6LxQazwqKcQzUcxRoTojoFiTDqi1j2X
```
