# Puzzle #183 Solution

- **Locking script**: `OP_DUP OP_HASH160 7470fb987a975b7488444fcf52cfea8975982c93 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `7470fb987a975b7488444fcf52cfea8975982c93`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 74 70 fb 98 7a 97 5b 74 88 44 4f cf 52 cf ea 89 75 98 2c 93`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `3d a5 36 40`
- **Base58Check encoding**: `1BcgjSCuu86nAXkpsvGPqtd3gYX9d4aMMH`

Therefore, the completed Bitcoin address for the given locking script is:

```
1BcgjSCuu86nAXkpsvGPqtd3gYX9d4aMMH
```
