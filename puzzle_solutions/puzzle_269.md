# Puzzle #269 Solution

- **Provided hash160**: `a477252d352b1a85661f9246e4bbb83d795fb58b`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 a4 77 25 2d 35 2b 1a 85 66 1f 92 46 e4 bb b8 3d 79 5f b5 8b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `30 df 38 79`
- **Base58Check encoding**: `1FzcYpHbTrDiX5PwrnRLxFkpihRtL3wLMN`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1FzcYpHbTrDiX5PwrnRLxFkpihRtL3wLMN
```

> **Note**: The puzzle metadata lists the address `1HN82JjK6eQ8wfQN2h2ora1MsE6uMFrXCL`. Decoding that Base58 string corresponds to a different hash160, so it does not match the supplied locking script.
