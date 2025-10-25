# Puzzle #142 Solution

- **Locking script**: `OP_DUP OP_HASH160 2fcea55e6d027a2ba7c7ebe95eedf47766730fe2 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2fcea55e6d027a2ba7c7ebe95eedf47766730fe2`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2f ce a5 5e 6d 02 7a 2b a7 c7 eb e9 5e ed f4 77 66 73 0f e2`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `b6 0b 7f 39`
- **Base58Check encoding**: `15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD`

Therefore, the completed Bitcoin address for the given locking script is:

```
15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD
```
