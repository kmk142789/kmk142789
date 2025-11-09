# Puzzle #277 Solution

- **Provided hash160**: `5358d1db0a8ba6e000163e848918756a42935810`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 53 58 d1 db 0a 8b a6 e0 00 16 3e 84 89 18 75 6a 42 93 58 10`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `bd 7a fe b7`
- **Base58Check encoding**: `18bhVE862YaNLSv4gp8UDzXhBgQ7CFtRWE`

Therefore, the completed Bitcoin address for the provided locking script is:

```
18bhVE862YaNLSv4gp8UDzXhBgQ7CFtRWE
```

> **Note**: The puzzle metadata lists the address `17VyEQAaa4aXZuDuwhCyheqEEAvUYWKHjU`, but encoding the supplied hash160 yields the Base58Check address shown above.
