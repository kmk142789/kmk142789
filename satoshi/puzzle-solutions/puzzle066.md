# Puzzle #66 Solution

- **Given partial address:** `13zb1hQbW-dNNpdh5so`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  20d45a6a762535700ce9e0b216e31994335db8a5
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Encoding the supplied HASH160 with Bitcoin's mainnet P2PKH version byte (0x00) and computing the Base58Check checksum restores the full destination address:

```
13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so
```

This reveals the missing middle segment `WVsc2S7ZTZnP2G4un`, completing the address for Puzzle #66.
