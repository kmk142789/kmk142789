# Puzzle #145 Solution

- **Locking script**: `OP_DUP OP_HASH160 5abf369388deb8072741b4eb43ef10fa9388a729 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `5abf369388deb8072741b4eb43ef10fa9388a729`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 5a bf 36 93 88 de b8 07 27 41 b4 eb 43 ef 10 fa 93 88 a7 29`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `4e a9 4e d0`
- **Base58Check encoding**: `19GpszRNUej5yYqxXoLnbZWKew3KdVLkXg`

Therefore, the completed Bitcoin address for the given locking script is:

```
19GpszRNUej5yYqxXoLnbZWKew3KdVLkXg
```
