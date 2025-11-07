# Puzzle #159 Solution

- **Locking script**: `OP_DUP OP_HASH160 1f4f410a377e63abbd56587c9ffec3f2c1f518ba OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `1f4f410a377e63abbd56587c9ffec3f2c1f518ba`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 1f 4f 41 0a 37 7e 63 ab bd 56 58 7c 9f fe c3 f2 c1 f5 18 ba`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `52 8e 3e e5`
- **Base58Check encoding**: `13rYtchcCNnLqox1BXrN7P8DaKnJr55iyr`

Therefore, the completed Bitcoin address for the given locking script is:

```
13rYtchcCNnLqox1BXrN7P8DaKnJr55iyr
```
