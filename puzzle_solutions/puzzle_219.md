# Puzzle #219 Solution

- **Provided P2PKH locking script**:
  ```
  OP_DUP OP_HASH160 55dbc5d954041104f71234723f96cb2f8450939c OP_EQUALVERIFY OP_CHECKSIG
  ```
- **Extracted hash160**: `55dbc5d954041104f71234723f96cb2f8450939c`
- **Bitcoin network version byte**: `0x00` (mainnet P2PKH)
- **Payload**: `00 55 db c5 d9 54 04 11 04 f7 12 34 72 3f 96 cb 2f 84 50 93 9c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))`
- **Base58Check encoding**: `18pyiPfQTQsLZ8xz3hEbowKoLrNXhEEMqy`

Therefore, the complete Bitcoin address that matches the given script is:

```
18pyiPfQTQsLZ8xz3hEbowKoLrNXhEEMqy
```
