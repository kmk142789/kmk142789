# Puzzle #69 Solution

- **Given partial address:** `19vkiEajf-qZbWqhxhG`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  61eb8a50c86b0584bb727dd65bed8d2400d6d5aa
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Encoding the supplied HASH160 with the Bitcoin mainnet P2PKH version byte (0x00) recovers the complete legacy address:

```
19vkiEajfhuZ8bs8Zu2jgmC6oqZbWqhxhG
```

This fills in the missing core segment `huZ8bs8Zu2jgmC6oq` and confirms the canonical destination for Puzzle #69.
