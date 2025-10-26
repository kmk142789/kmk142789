# Puzzle #182 Solution

- **Locking script**: `OP_DUP OP_HASH160 1eae732b6150e1b3ea4ea335534290044d2f41ba OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `1eae732b6150e1b3ea4ea335534290044d2f41ba`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 1e ae 73 2b 61 50 e1 b3 ea 4e a3 35 53 42 90 04 4d 2f 41 ba`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `60 f9 2e 88`
- **Base58Check encoding**: `13oEFkDaLbacehDeHn3bvEWbjdaS6Q2AX1`

Therefore, the completed Bitcoin address for the given locking script is:

```
13oEFkDaLbacehDeHn3bvEWbjdaS6Q2AX1
```
