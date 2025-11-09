# Puzzle #281 Solution

- **Provided hash160**: `56896864a21a26fa2509dde5872b877d912d9510`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 56 89 68 64 a2 1a 26 fa 25 09 dd e5 87 2b 87 7d 91 2d 95 10`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `88 8c 89 a6`
- **Base58Check encoding**: `18tZikx1FfgDaiWQAzuTps2YRGFJeQdSWZ`

Therefore, the completed Bitcoin address for the provided locking script is:

```
18tZikx1FfgDaiWQAzuTps2YRGFJeQdSWZ
```

> **Note**: The puzzle metadata lists the address `12pLswxvVN2bNZ81WCEEf2y7sj2eAEBz4N`, but decoding that Base58 string yields a
 different hash160 and an invalid checksum, so it does not match the supplied locking script.
