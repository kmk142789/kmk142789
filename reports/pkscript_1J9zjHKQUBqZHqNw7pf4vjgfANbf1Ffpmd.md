# PKScript Analysis: 1J9zjHKQUBqZHqNw7pf4vjgfANbf1Ffpmd

## Summary
The supplied transcript matches the classic pay-to-public-key (P2PK) format that Satoshi used in the early puzzle transactions. Restoring the hidden middle run of characters in the heading converts the redacted string `1J9zjHKQU-Nbf1Ffpmd` into the full legacy address `1J9zjHKQUBqZHqNw7pf4vjgfANbf1Ffpmd`.

```
1J9zjHKQU-Nbf1Ffpmd
Pkscript
04001fcc53548c60917ac2b63f35551557a0cb78404b66e6c9e070ca146413ef62ecc13535c3cedf6d04d1e02f9052536ca9a0c67aa8a618b7d40da1db40f1e6c3
OP_CHECKSIG
```

## Details
- **Public key:** `04001fcc53548c60917ac2b63f35551557a0cb78404b66e6c9e070ca146413ef62ecc13535c3cedf6d04d1e02f9052536ca9a0c67aa8a618b7d40da1db40f1e6c3`
- **Script hex:** `4104001fcc53548c60917ac2b63f35551557a0cb78404b66e6c9e070ca146413ef62ecc13535c3cedf6d04d1e02f9052536ca9a0c67aa8a618b7d40da1db40f1e6c3ac`
- **Derived P2PKH address:** Hashing the supplied public key with SHA-256 followed by RIPEMD-160 and encoding with Base58Check yields `1J9zjHKQUBqZHqNw7pf4vjgfANbf1Ffpmd`.
- **Missing segment:** The hyphen replaces the infix `BqZHqNw7pf4vjgfA`. Reinserting it produces the complete address shown above.

## Reproduction
The repository helper confirms the reconstruction:

```
python tools/pkscript_to_address.py <<'EOF'
1J9zjHKQU-Nbf1Ffpmd
Pkscript
04001fcc53548c60917ac2b63f35551557a0cb78404b66e6c9e070ca146413ef62ecc13535c3cedf6d04d1e02f9052536ca9a0c67aa8a618b7d40da1db40f1e6c3
OP_CHECKSIG
EOF
```

Running the command emits `1J9zjHKQUBqZHqNw7pf4vjgfANbf1Ffpmd`, validating the P2PK interpretation and the restored Base58 address.
