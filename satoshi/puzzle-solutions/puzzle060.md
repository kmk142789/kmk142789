# Puzzle #60 Solution

- **Given partial address:** `1Kn5h2qpg-vJ1QVy8su`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  cdf8e5c7503a9d22642e3ecfc87817672787b9c5
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Base58Check-encoding the supplied HASH160 with the Bitcoin mainnet P2PKH version byte (0x00) reconstructs the complete destination address:

```
1Kn5h2qpgw9mWE5jKpk8PP4qvvJ1QVy8su
```

This reveals the missing middle segment `w9mWE5jKpk8PP4qv`, restoring the full address for Puzzle #60.
