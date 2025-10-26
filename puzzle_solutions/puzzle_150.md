# Puzzle #150 Solution

- **Locking script**: `OP_DUP OP_HASH160 e08c4d3bc9cf2b3e2cb88de2bfaa4fe8c7aa3f24 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `e08c4d3bc9cf2b3e2cb88de2bfaa4fe8c7aa3f24`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 e0 8c 4d 3b c9 cf 2b 3e 2c b8 8d e2 bf aa 4f e8 c7 aa 3f 24`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `0a d9 15 e0`
- **Base58Check encoding**: `1MUJSJYtGPVGkBCTqGspnxyHahpt5Te8jy`

Therefore, the completed Bitcoin address for the given locking script is:

```
1MUJSJYtGPVGkBCTqGspnxyHahpt5Te8jy
```
