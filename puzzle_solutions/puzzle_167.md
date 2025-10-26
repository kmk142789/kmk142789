# Puzzle #167 Solution

- **Locking script**: `OP_DUP OP_HASH160 9cfc3e9a98591a2f4212e8d56f11dac521b45991 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `9cfc3e9a98591a2f4212e8d56f11dac521b45991`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 9c fc 3e 9a 98 59 1a 2f 42 12 e8 d5 6f 11 da c5 21 b4 59 91`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `c1 62 9b 2b`
- **Base58Check encoding**: `12hf1Y53zc7ezTdFPxQ5KAU3jHD3Th1R3K`

Therefore, the completed Bitcoin address for the given locking script is:

```
12hf1Y53zc7ezTdFPxQ5KAU3jHD3Th1R3K
```
