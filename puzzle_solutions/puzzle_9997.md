# Puzzle #9997 Solution

- **Provided hash160**: `65b375b639ccc35a956cd7a8ef0ab41bdd8ce059`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 65 b3 75 b6 39 cc c3 5a 95 6c d7 a8 ef 0a b4 1b dd 8c e0 59`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `51 1c 3a ca`
- **Base58Check encoding**: `1AGkETkTR6JnEMd5vEjzz1qFKZjzG3BpJ5`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1AGkETkTR6JnEMd5vEjzz1qFKZjzG3BpJ5
```

> **Note**: The puzzle metadata lists the address `1Br4gfJVyc124jViD8Ktpxb6u4L2SF6KTf`, but decoding that Base58 string yields a
> different payload and checksum, so it does not correspond to the supplied hash160.
