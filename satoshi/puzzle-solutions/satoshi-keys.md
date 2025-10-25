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

## Second shared key fragment

- **Given partial address:** `162dTd1RG-3vFQ1DpgA`
- **Provided P2PK script:**
  ```
  04001a23137d302f70eb0f78af6009262c85588562c1ba5e214052506393d36cb654af995cbba0c6a46533da7da895047965e619dd0c862bf340d2f235b3301
  69b
  OP_CHECKSIG
  ```

Decoding the uncompressed public key reveals the HASH160 fingerprint `37277ab3ad1c32e2a166045bd1591d95f6e1c1d1` and reproduces the
complete Base58Check address:

```
162dTd1RGztAFZ9YMmFZEpKuz3vFQ1DpgA
```

This fills in the missing middle segment `ztAFZ9YMmFZEpKuz`, recovering the destination hinted at by the second "Satoshi keys" clue.

To confirm the reconstruction on your own machine, run:

```bash
python -m tools.pkscript_decoder --pubkey \
  04001a23137d302f70eb0f78af6009262c85588562c1ba5e214052506393d36cb654af995cbba0c6a46533da7da895047965e619dd0c862bf340d2f235b3301
  69b
```
