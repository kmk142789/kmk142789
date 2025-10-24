# PKScript Analysis: 1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74

## Summary
The provided program is a canonical pay-to-public-key-hash (P2PKH) locking
script. It duplicates the prospective spending public key with `OP_DUP`, hashes
the duplicate via `OP_HASH160`, compares the 20-byte hash against the embedded
value using `OP_EQUALVERIFY`, and finally applies `OP_CHECKSIG` to demand a
valid ECDSA signature.

```
Pkscript
OP_DUP
OP_HASH160
9978f61b92d16c5f1a463a0995df70da1f7a7d2a
OP_EQUALVERIFY
OP_CHECKSIG
```

Any unlocking script must therefore supply a public key whose HASH160 equals
`9978f61b92d16c5f1a463a0995df70da1f7a7d2a` along with a DER-encoded signature
that validates against the referenced transaction data.

## Derived address
Applying the Base58Check algorithm for a mainnet P2PKH output—prefixing the
HASH160 with version byte `0x00`, calculating the double-SHA256 checksum, and
encoding with the Bitcoin alphabet—produces the address
`1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74`.

## Reproduction
The repository helper can regenerate the address directly from the pasted
script fragment:

```
python tools/pkscript_to_address.py <<'EOF'
Pkscript
OP_DUP
OP_HASH160
9978f61b92d16c5f1a463a0995df70da1f7a7d2a
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running the command yields `1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74`, confirming the
interpretation above.
