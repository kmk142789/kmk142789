# Puzzle #160 Solution

- **Locking script**: `OP_DUP OP_HASH160 e84818e1bf7f699aa6e28ef9edfb582099099292 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `e84818e1bf7f699aa6e28ef9edfb582099099292`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 e8 48 18 e1 bf 7f 69 9a a6 e2 8e f9 ed fb 58 20 99 09 92 92`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `5d 35 16 99`
- **Base58Check encoding**: `1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv
```
