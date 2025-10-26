# Puzzle #166 Solution

- **Locking script**: `OP_DUP OP_HASH160 fcbd42f0e970467a2cbc365ab23920812ec00523 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `fcbd42f0e970467a2cbc365ab23920812ec00523`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 fc bd 42 f0 e9 70 46 7a 2c bc 36 5a b2 39 20 81 2e c0 05 23`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `48 27 ae 60`
- **Base58Check encoding**: `18hG3rvCsBprktL6KSeVrwc6GwbaWW6Arc`

Therefore, the completed Bitcoin address for the given locking script is:

```
18hG3rvCsBprktL6KSeVrwc6GwbaWW6Arc
```
