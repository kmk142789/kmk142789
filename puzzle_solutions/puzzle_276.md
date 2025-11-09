# Puzzle #276 Solution

- **Provided hash160**: `4ff600559ea792ae909ed1713c471cf653c7cfc6`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 4f f6 00 55 9e a7 92 ae 90 9e d1 71 3c 47 1c f6 53 c7 cf c6`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `65 c1 f0 10`
- **Base58Check encoding**: `18Ho5dFbCyEAxtCpxEHpZv9SLCS5q3ieNK`

Therefore, the completed Bitcoin address for the provided locking script is:

```
18Ho5dFbCyEAxtCpxEHpZv9SLCS5q3ieNK
```

> **Note**: The puzzle metadata lists the address `1AzBjsrQ8DK1WxkTqtzYnVDyoGxS4vQfgD`, but decoding that Base58 string yields a
> different hash160 (and checksum), so it does not match the supplied locking script.
