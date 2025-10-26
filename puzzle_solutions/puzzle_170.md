# Puzzle #170 Solution

- **Locking script**: `OP_DUP OP_HASH160 ed1026f94bed5f2d0bca03aceb258f48bfbbfc85 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `ed1026f94bed5f2d0bca03aceb258f48bfbbfc85`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 ed 10 26 f9 4b ed 5f 2d 0b ca 03 ac eb 25 8f 48 bf bb fc 85`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `e1 0a 5f 4d`
- **Base58Check encoding**: `1J2K6weoPf9QevSCmzQfeJZGDYUH7NHA9T`

Therefore, the completed Bitcoin address for the given locking script is:

```
1J2K6weoPf9QevSCmzQfeJZGDYUH7NHA9T
```
