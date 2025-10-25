# Puzzle #51 Solution

- **Given partial address:** `1NpnQyZ7x-N8bqGQnaS`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  ef6419cffd7fad7027994354eb8efae223c2dbe7
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Encoding the supplied HASH160 with the mainnet P2PKH version byte (0x00) and appending the Base58Check checksum restores the full Bitcoin address:

```
1NpnQyZ7x24ud82b7WiRNvPm6N8bqGQnaS
```

This reveals the missing middle segment `24ud82b7WiRNvPm6`, completing the destination address for Puzzle #51.
