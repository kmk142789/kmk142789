# Puzzle #157 Solution

- **Locking script**: `OP_DUP OP_HASH160 242d790e5a168043c76f0539fd894b73ee67b3b3 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `242d790e5a168043c76f0539fd894b73ee67b3b3`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 24 2d 79 0e 5a 16 80 43 c7 6f 05 39 fd 89 4b 73 ee 67 b3 b3`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `e9 a5 20 46`
- **Base58Check encoding**: `14JHoRAdmJg3XR4RjMDh6Wed6ft6hzbQe9`

Therefore, the completed Bitcoin address for the given locking script is:

```
14JHoRAdmJg3XR4RjMDh6Wed6ft6hzbQe9
```
