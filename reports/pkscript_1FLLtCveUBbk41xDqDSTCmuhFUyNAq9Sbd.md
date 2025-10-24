# PKScript Analysis: 1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd

## Summary
The provided program is the canonical pay-to-public-key-hash (P2PKH) locking script format used by legacy Bitcoin addresses. It duplicates the spending public key, hashes it with `OP_HASH160`, compares the result against the embedded 20-byte hash using `OP_EQUALVERIFY`, and finishes with `OP_CHECKSIG` to require a valid ECDSA signature.

```
Pkscript
OP_DUP
OP_HASH160
9d3a42f96f59d145f9d722004be4390540ccc752
OP_EQUALVERIFY
OP_CHECKSIG
```

Hashing the decoded public key during redemption must reproduce the in-script hash above. When that condition is satisfied, a DER-encoded signature that validates against the supplied public key finalises the spend.

## Derived address
Applying the standard Base58Check encoding flow for a mainnet P2PKH script—prefixing the hash with the `0x00` version byte and appending the four-byte double-SHA256 checksum—produces the Bitcoin address `1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd`.

## Reproduction
The repository helper can regenerate the address directly from the pasted script fragment:

```
python tools/pkscript_to_address.py <<'EOF'
Pkscript
OP_DUP
OP_HASH160
9d3a42f96f59d145f9d722004be4390540ccc752
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running the command yields `1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd`, confirming the interpretation above.
