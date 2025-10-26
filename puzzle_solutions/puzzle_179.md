# Puzzle #179 Solution

- **Locking script**: `OP_DUP OP_HASH160 d09106e69af7794ea17f2cbc2366aa5baba81e57 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `d09106e69af7794ea17f2cbc2366aa5baba81e57`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 d0 91 06 e6 9a f7 79 4e a1 7f 2c bc 23 66 aa 5b ab a8 1e 57`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `77 b1 97 6f`
- **Base58Check encoding**: `1L1oHYvDqvv33jb65ZT6xMr7Mi1k8ZqVgA`

Therefore, the completed Bitcoin address for the given locking script is:

```
1L1oHYvDqvv33jb65ZT6xMr7Mi1k8ZqVgA
```
