# Puzzle #137 Solution

- **Locking script**: `OP_DUP OP_HASH160 60906771fa85ba6ab9ca11bd49a991b1dec507c7 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `60906771fa85ba6ab9ca11bd49a991b1dec507c7`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 60 90 67 71 fa 85 ba 6a b9 ca 11 bd 49 a9 91 b1 de c5 07 c7`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `75 f4 d0 ee`
- **Base58Check encoding**: `19oarnfUSLBfscLAJ1X2oTNtubZcQGnsfs`

Therefore, the completed Bitcoin address for the given locking script is:

```
19oarnfUSLBfscLAJ1X2oTNtubZcQGnsfs
```
