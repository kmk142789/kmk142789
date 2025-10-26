# Puzzle #184 Solution

- **Locking script**: `OP_DUP OP_HASH160 3194cf18043af36e73ec1cf43ee52256a4f6cd22 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `3194cf18043af36e73ec1cf43ee52256a4f6cd22`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 31 94 cf 18 04 3a f3 6e 73 ec 1c f4 3e e5 22 56 a4 f6 cd 22`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `fd e8 90 9c`
- **Base58Check encoding**: `15XANpzjqmxNgGoJ1CMw1U1p1myhFE4u2B`

Therefore, the completed Bitcoin address for the given locking script is:

```
15XANpzjqmxNgGoJ1CMw1U1p1myhFE4u2B
```
