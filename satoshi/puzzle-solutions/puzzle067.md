# Puzzle #67 Solution

- **Given partial address:** `1BY8GQbnu-jPrkxDdW9`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  739437bb3dd6d1983e66629c5f08c70e52769371
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Applying the Bitcoin mainnet P2PKH version byte (0x00) to the supplied HASH160, then computing and appending the Base58Check checksum, reconstructs the complete address:

```
1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9
```

This reveals the missing middle segment `eYofwSuFAT3USAhGjPrk`, restoring the destination address for Puzzle #67.
