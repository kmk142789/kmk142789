# Puzzle #63 Solution

- **Given partial address:** `1NpYjtLir-h3ai9bjf4`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  ef58afb697b094423ce90721fbb19a359ef7c50e
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Encoding the supplied HASH160 with the mainnet P2PKH version byte (0x00) and appending the Base58Check checksum restores the full Bitcoin address:

```
1NpYjtLira16LfGbGwZJ5JbDPh3ai9bjf4
```

This reveals the missing middle segment `a16LfGbGwZJ5JbDP`, completing the destination address for Puzzle #63.
