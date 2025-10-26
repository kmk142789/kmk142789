# Puzzle #148 Solution

- **Locking script**: `OP_DUP OP_HASH160 a3e3612e586fd206efb8eee6ccd58318e182829a OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `a3e3612e586fd206efb8eee6ccd58318e182829a`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 a3 e3 61 2e 58 6f d2 06 ef b8 ee e6 cc d5 83 18 e1 82 82 9a`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `e0 d0 a0 06`
- **Base58Check encoding**: `1FwZXt6EpRT7Fkndzv6K4b4DFoT4trbMrV`

Therefore, the completed Bitcoin address for the given locking script is:

```
1FwZXt6EpRT7Fkndzv6K4b4DFoT4trbMrV
```
