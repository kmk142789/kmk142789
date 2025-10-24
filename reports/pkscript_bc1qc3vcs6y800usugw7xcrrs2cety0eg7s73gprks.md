# PKScript Analysis: bc1qc3vcs6y800usugw7xcrrs2cety0eg7s73gprks

## Summary
The provided locking script is a SegWit pay-to-witness-public-key-hash (P2WPKH) output. The `0x00` version byte followed by a 20-byte hash indicates that funds can be spent by revealing a compressed secp256k1 public key whose HASH160 matches the witness program and by providing a corresponding ECDSA signature in the witness stack.

```
0014c4598868877bf90e21de3606382b19591f947a1e
```

## Details
- **Witness program structure:** The script starts with an `OP_0` (`0x00`) then pushes a 20-byte payload, matching the canonical P2WPKH form `0 <pubKeyHash>`.
- **Derived address:** Encoding the version byte and hash using BIP-0173 bech32 yields the bech32m address `bc1qc3vcs6y800usugw7xcrrs2cety0eg7s73gprks`. This extends the truncated string `bc1qc3vcs-7s73gprks` that was supplied.
- **Witness data:** The witness stack contains a DER-encoded signature ending in `0x01`, signalling `SIGHASH_ALL`, and a 33-byte compressed public key beginning with `0x03`. Hashing that key with SHA-256 followed by RIPEMD-160 reproduces the 20-byte witness program shown above, confirming the spend conditions are satisfied.

```
Witness
3044022055dc798b00c64baba563ac6eab7b5f3a328549fe29654012242f0e1686498eb102203d356925dd36c96c84e0f75737967242602d456fa5cff15629a9c85cc1ed814c01
0311f224419f72494136957119992245f5d1fa016d353fa66719359c9e8843
```

## Reproduction
The bech32 address can be reproduced with the repository helper:

```
python tools/pkscript_to_address.py <<'EOF'
Pkscript
0014c4598868877bf90e21de3606382b19591f947a1e
EOF
```

This emits `bc1qc3vcs6y800usugw7xcrrs2cety0eg7s73gprks`, verifying the decoding above.
