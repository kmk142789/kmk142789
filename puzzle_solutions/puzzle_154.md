# Puzzle #154 Solution

- **Locking script**: `OP_DUP OP_HASH160 3a4adaa4ac15018c5ab6c28dcc2e1e2ce050c939 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `3a4adaa4ac15018c5ab6c28dcc2e1e2ce050c939`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 3a 4a da a4 ac 15 01 8c 5a b6 c2 8d cc 2e 1e 2c e0 50 c9 39`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `12 31 17 4b`
- **Base58Check encoding**: `12KbdGkuZDsUETVUahgLVq4SofF7rRdP5j`

Therefore, the completed Bitcoin address for the given locking script is:

```
12KbdGkuZDsUETVUahgLVq4SofF7rRdP5j
```
