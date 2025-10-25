# Puzzle #108 Solution

- **Given partial address:** `1HB1iKUqe-XKbyNuqao`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  b166c44f12c7fc565f37ff6288ee64e0f0ec9a0b
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Base58Check-encoding the supplied HASH160 with the Bitcoin mainnet P2PKH version byte (0x00) reconstructs the complete destination address:

```
1HB1iKUqeffnVsvQsbpC6dNi1XKbyNuqao
```

This uncovers the missing middle segment `ffnVsvQsbpC6dNi1`, restoring the full address for Puzzle #108.
