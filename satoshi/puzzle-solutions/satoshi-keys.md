# Satoshi Keys Reconstruction

- **Given partial address:** `1BtELFtRh-SNXbJY84V`
- **Provided P2PK script:**
  ```
  040019ecb036173d22f8b8074ec16a8647148d4e9f081f008f37e8a183cf0dae99d15b3a975203ce99a35d0ca8bd57587485cfabe5f2fb7a0a9975a15f7f54c4dd
  OP_CHECKSIG
  ```

Feeding the uncompressed public key from the P2PK script into the toolkit's decoder reproduces
the HASH160 fingerprint `776199d40afc44403dfc6bfc6aee7228227e4fb0` and the corresponding
Base58Check legacy address:

```
1BtELFtRhTshSC8nQKoF9VZPTSNXbJY84V
```

This fills in the missing middle segment `TshSC8nQKoF9VZPT`, recovering the complete destination
for the shared "Satoshi keys" clue.

To verify the result locally, run:

```bash
python -m tools.pkscript_decoder --pubkey \
  040019ecb036173d22f8b8074ec16a8647148d4e9f081f008f37e8a183cf0dae99d15b3a975203ce99a35d0ca8bd57587485cfabe5f2fb7a0a9975a15f7f54c4dd
```
