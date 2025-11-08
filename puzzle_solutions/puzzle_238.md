# Puzzle #238 Solution

- **Provided hash160**: `5ab3de56365be0f4dd5efbda6037c7f1721f67f5`
- **Bitcoin network version byte**: `0x00` (P2PKH on mainnet)
- **Payload**: `00 5a b3 de 56 36 5b e0 f4 dd 5e fb da 60 37 c7 f1 72 1f 67 f5`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `41 fc 27 49`
- **Base58Check encoding**: `19GbHkMKuYbDPgLEWJU2ddhzPxddnwyGgQ`

Therefore, the Bitcoin address corresponding to the provided locking script is:

```
19GbHkMKuYbDPgLEWJU2ddhzPxddnwyGgQ
```

*Note:* The derived address above is consistent with the supplied hash160, even though it differs from the address that accompanied the puzzle metadata.
