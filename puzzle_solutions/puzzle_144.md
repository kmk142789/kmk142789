# Puzzle #144 Solution

- **Locking script**: `OP_DUP OP_HASH160 ed87120066e244ff5331d5f8625873d7a3acc39c OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `ed87120066e244ff5331d5f8625873d7a3acc39c`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 ed 87 12 00 66 e2 44 ff 53 31 d5 f8 62 58 73 d7 a3 ac c3 9c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `32 9f 9b c3`
- **Base58Check encoding**: `1NevxKDYuDcCh1ZMMi6ftmWwGrZKC6j7Ux`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NevxKDYuDcCh1ZMMi6ftmWwGrZKC6j7Ux
```
