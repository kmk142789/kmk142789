# Puzzle #154 Solution

- **Locking script**: `OP_DUP OP_HASH160 edd2e206825fa8949d1304cd82c08d64b222f2eb OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `edd2e206825fa8949d1304cd82c08d64b222f2eb`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 ed d2 e2 06 82 5f a8 94 9d 13 04 cd 82 c0 8d 64 b2 22 f2 eb`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `7a 51 ca 03`
- **Base58Check encoding**: `1NgVmsCCJaKLzGyKLFJfVequnFW9ZvnMLN`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NgVmsCCJaKLzGyKLFJfVequnFW9ZvnMLN
```
