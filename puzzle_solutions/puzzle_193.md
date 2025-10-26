# Puzzle #193 Solution

- **Locking script**: `OP_DUP OP_HASH160 d4bad4594c12dff42b054b70bf2bf392fd6e5239 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `d4bad4594c12dff42b054b70bf2bf392fd6e5239`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 d4 ba d4 59 4c 12 df f4 2b 05 4b 70 bf 2b f3 92 fd 6e 52 39`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `f3 5d 7a 6c`
- **Base58Check encoding**: `1LPp4otXQ3siKUDaJisivQftaC6ieGGUR9`

Therefore, the completed Bitcoin address for the given locking script is:

```
1LPp4otXQ3siKUDaJisivQftaC6ieGGUR9
```
