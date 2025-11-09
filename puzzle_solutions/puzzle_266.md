# Puzzle #266 Solution

- **Provided hash160**: `08c288f0925cc3fe410793902fad11dda4537342`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 08 c2 88 f0 92 5c c3 fe 41 07 93 90 2f ad 11 dd a4 53 73 42`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `49 d6 f1 25`
- **Base58Check encoding**: `1oKT4Mneqjq8m1PJV4g1baDzxFHACr21A`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1oKT4Mneqjq8m1PJV4g1baDzxFHACr21A
```

> **Note**: The metadata lists the address `18EugTfo4znuGNxPY2yUDR8nxJstZF378C`, but decoding that Base58 string yields the
> hash160 `4f6a43693754f11db0b8c81b7e4e9ae6c00b4b3a` and the checksum `628aee69` (expected `908a1d4a`), so it does not
> correspond to the supplied locking script.
