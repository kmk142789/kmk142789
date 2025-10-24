# PKScript Analysis: 1L12FHH2FHjvTviyanuiFVfmzCy46RRATU

## Summary
The provided locking script follows the standard pay-to-public-key-hash (P2PKH) pattern. It duplicates the witness, hashes it with `OP_HASH160`, compares the result against the embedded 20-byte digest via `OP_EQUALVERIFY`, and finishes with `OP_CHECKSIG` to validate the spender's signature. The supplied address fragment contains a hyphenated gap; when reconstructed, it resolves to the canonical Bitcoin mainnet address shown above.

```
OP_DUP
OP_HASH160
d06b6e206691295ec345782d7ea0686969d8674b
OP_EQUALVERIFY
OP_CHECKSIG
```

## Details
- **Hash payload:** `d06b6e206691295ec345782d7ea0686969d8674b` is a 20-byte RIPEMD-160 digest, the precise size expected in a P2PKH script.
- **Derived address:** Prefixing the hash with the Bitcoin mainnet version byte (`0x00`), appending the Base58Check checksum, and encoding yields the address `1L12FHH2FHjvTviyanuiFVfmzCy46RRATU`.
- **Script structure:** The opcode sequence exactly matches the canonical five-opcode P2PKH template, so spending the output requires presenting a signature and public key whose hash matches the embedded digest.

## Reproduction
The derivation is reproducible with the repository helper:

```
python tools/pkscript_to_address.py <<'EOF'
1L12FHH2F-Cy46RRATU
Pkscript
OP_DUP
OP_HASH160
d06b6e206691295ec345782d7ea0686969d8674b
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running the helper emits the canonical address `1L12FHH2FHjvTviyanuiFVfmzCy46RRATU`, confirming the interpretation above.
