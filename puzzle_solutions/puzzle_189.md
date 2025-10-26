# Puzzle #189 Solution

- **Locking script**: `OP_DUP OP_HASH160 fb8494fc6fe25f71862776926f3dd663c9e72e98 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `fb8494fc6fe25f71862776926f3dd663c9e72e98`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 fb 84 94 fc 6f e2 5f 71 86 27 76 92 6f 3d d6 63 c9 e7 2e 98`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `b4 6e d3 59`
- **Base58Check encoding**: `1PvuS7Bteu1j8X9ZWjrdDgnVUScmrsuhFn`

Therefore, the completed Bitcoin address for the given locking script is:

```
1PvuS7Bteu1j8X9ZWjrdDgnVUScmrsuhFn
```
