# Puzzle #256 Solution

- **Provided hash160**: `84600e171a945255218708fe92f53773c8aa9bc4`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 84 60 0e 17 1a 94 52 55 21 87 08 fe 92 f5 37 73 c8 aa 9b c4`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `67 89 58 e1`
- **Base58Check encoding**: `1D4wGLtBWJbtJny8z4mqommhyzduWen17E`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1D4wGLtBWJbtJny8z4mqommhyzduWen17E
```

> **Note**: The metadata lists the address `1GF3A7DHQQ4A3f3mqRtMkH796FDkCtmgWz`, but decoding that Base58 string yields the hash160 `a73182c47977adbf23b56db3c46ed6d75cff88e0`, which does not match the supplied locking script. The Base58Check reconstruction above is the correct address for this puzzle.
