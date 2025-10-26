# PKScript Analysis: 1AvLwGpkwTZH4qiwy1L4v6TuWXLMNrATN5

## Summary
The provided transcript is another P2PKH locking script.  Its HASH160 payload
encodes the mainnet address `1AvLwGpkwTZH4qiwy1L4v6TuWXLMNrATN5` once the
redacted Base58Check characters are restored.

## Details
- **Hash target:** `6ccfd1cdb43788738536e11e247b0ce31c093f0f` is the 20-byte
  HASH160 digest pushed between `OP_HASH160` and `OP_EQUALVERIFY`.  Combined with
  the surrounding `OP_DUP` and `OP_CHECKSIG` opcodes it forms the textbook
  P2PKH locking program.
- **Label reconstruction:** The heading `1AvLwGpkw-XLMNrATN5` omits the middle
  of the Base58 string.  Re-inserting the missing run `TZH4qiwy1L4v6TuW`
  reproduces the full address above.
- **Spend metadata:** The `Sigscript` section supplies a 72-byte DER signature
  (the `0x48` prefix) followed by a compressed public key (`0377…b4941`).  These
  unlocking values are specific to the spending transaction and leave the
  locking script unchanged.

## Reproduction
The repository helper confirms the derivation by ignoring the trailing spend
metadata and rebuilding the Base58Check address from the HASH160 payload:

```bash
python tools/pkscript_to_address.py <<'EOF'
1AvLwGpkw-XLMNrATN5
Pkscript
OP_DUP
OP_HASH160
6ccfd1cdb43788738536e11e247b0ce31c093f0f
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
483045022100ad63fba425caf2bf5bc3f8bd47423f8a279d41a97eb7c505c1a0c9d8ae06538d0220185180346c083b9366a65e07ad40bdace06bbff2dfc34de280814502405f2cd6012103779c01b4badc5c3883f6ea2b93214a24796154c8eb967695dfc802bf074b4941
Witness
EOF
```

Executing the command prints `1AvLwGpkwTZH4qiwy1L4v6TuWXLMNrATN5`, matching the
interpreted locking script.
