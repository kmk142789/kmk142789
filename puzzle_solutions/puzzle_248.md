# Puzzle #248 Solution

- **Provided hash160**: `08df482ffddf42b5f7e5e0801c717d9522a21ba6`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 08 df 48 2f fd df 42 b5 f7 e5 e0 80 1c 71 7d 95 22 a2 1b a6`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `5c a9 b8 a6`
- **Base58Check encoding**: `1outSSxSAucNP3qnVAwj52UXe8AHMQHX3`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1outSSxSAucNP3qnVAwj52UXe8AHMQHX3
```

> **Note**: The metadata field `1DhhcZspz4QEkY6eWSR7oPFRo2ZeeFW8PL` decodes to a different hash160 and does not match the supplied locking script, so the Base58Check reconstruction above is the correct address for this puzzle.
