# Puzzle #155 Solution

- **Locking script**: `OP_DUP OP_HASH160 e581fed67dab8e4bdb37c09699a26f98a5c0cc9e OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `e581fed67dab8e4bdb37c09699a26f98a5c0cc9e`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 e5 81 fe d6 7d ab 8e 4b db 37 c0 96 99 a2 6f 98 a5 c0 cc 9e`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `79 d4 68 ef`
- **Base58Check encoding**: `137sTFpStvaWxwXBsZu3x3TfnT5ZttYRkp`

Therefore, the completed Bitcoin address for the given locking script is:

```
137sTFpStvaWxwXBsZu3x3TfnT5ZttYRkp
```
