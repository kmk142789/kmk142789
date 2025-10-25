# Puzzle #101 Solution

- **Given partial address:** `1CKCVdbDJ-NaDpK7W4n`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  7c1a77205c03b9909663b2034faa0b544e6bc96b
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

The hash160 fingerprint `7c1a77205c03b9909663b2034faa0b544e6bc96b` corresponds to the Base58Check
Bitcoin address:

```
1CKCVdbDJasYmhswB6HKZHEAnNaDpK7W4n
```

This reveals the missing center segment `asYmhswB6HKZHEAn`, completing the destination for Puzzle #101.
