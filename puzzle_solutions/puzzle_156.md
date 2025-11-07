# Puzzle #156 Solution

- **Locking script**: `OP_DUP OP_HASH160 34f2e4b91e371389a23cb98f337ef1266c388716 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `34f2e4b91e371389a23cb98f337ef1266c388716`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 34 f2 e4 b9 1e 37 13 89 a2 3c b9 8f 33 7e f1 26 6c 38 87 16`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `3b 80 32 c4`
- **Base58Check encoding**: `18Sc1enJ9bBzfD4cZAowJiRdTGs6PoTv9n`

Therefore, the completed Bitcoin address for the given locking script is:

```
18Sc1enJ9bBzfD4cZAowJiRdTGs6PoTv9n
```
