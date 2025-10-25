# Puzzle #136 Solution

- **Locking script**: `OP_DUP OP_HASH160 de82bc058460220274c9c5096df72a167a3324f6 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `de82bc058460220274c9c5096df72a167a3324f6`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 de 82 bc 05 84 60 22 02 74 c9 c5 09 6d f7 2a 16 7a 33 24 f6`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `91 de 0d 2d`
- **Base58Check encoding**: `1MHXdBCUEbsycPCGadNYuTfUJnvPed7WHi`

Therefore, the completed Bitcoin address for the given locking script is:

```
1MHXdBCUEbsycPCGadNYuTfUJnvPed7WHi
```
