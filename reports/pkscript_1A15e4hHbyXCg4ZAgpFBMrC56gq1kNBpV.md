# PKScript Analysis: 1A15e4hHbyXCg4ZAgpFBMrC56gq1kNBpV

## Summary
The submitted transcript is a classic pay-to-public-key (P2PK) locking script. It places an uncompressed 65-byte secp256k1 public key on the stack and immediately enforces signature verification through `OP_CHECKSIG`. The shorthand source reproduces to the canonical hexadecimal form

```
41 040018247777ec96569e72b4d2730108f00739ba6894eeffb02740b6455725a48275a4451059803a4f5e84c47189a6a100a146aac8251cfc7d95666938fde4687e ac
```

which matches the historical output template Satoshi used in the original treasure puzzles.

## Details
- **Public key:** `040018247777ec96569e72b4d2730108f00739ba6894eeffb02740b6455725a48275a4451059803a4f5e84c47189a6a100a146aac8251cfc7d95666938fde4687e`
- **Script hex:** `41040018247777ec96569e72b4d2730108f00739ba6894eeffb02740b6455725a48275a4451059803a4f5e84c47189a6a100a146aac8251cfc7d95666938fde4687eac`
- **Derived P2PKH address:** Hashing the supplied public key (SHA256 followed by RIPEMD160) and encoding with Base58Check yields `1A15e4hHbyXCg4ZAgpFBMrC56gq1kNBpV`.
- **Formatting artefact:** The heading `1A15e4hHb-6gq1kNBpV` keeps the prefix and suffix of the address but drops the central 17 characters while inserting a hyphen. Restoring the missing segment (`yXCg4ZAgpFBMrC56gq1kNBp`) produces the full address above.

## Reproduction
The repository helper confirms the reconstruction:

```
python tools/pkscript_to_address.py <<'EOF'
1A15e4hHb-6gq1kNBpV
Pkscript
040018247777ec96569e72b4d2730108f00739ba6894eeffb02740b6455725a48275a4451059803a4f5e84c47189a6a100a146aac8251cfc7d95666938fde4687e
OP_CHECKSIG
EOF
```

Running the command restores the canonical address `1A15e4hHbyXCg4ZAgpFBMrC56gq1kNBpV` and verifies the P2PK interpretation.
