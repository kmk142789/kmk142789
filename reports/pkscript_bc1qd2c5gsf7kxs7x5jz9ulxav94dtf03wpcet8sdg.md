# PKScript Analysis: bc1qd2c5gsf7kxs7x5jz9ulxav94dtf03wpcet8sdg

## Summary
The transcript describes a native SegWit pay-to-witness-public-key-hash (P2WPKH) output. The `OP_0` prefix and 20-byte witness program confirm a version-0 bech32 address. The UTXO was later spent by transaction `8160ce342025b9141b9dfc398936449f3c04de41de13818c6ef245707285a4b2` in block 916418.

```
Type
V0_P2WPKH
scriptPubKey (asm)
OP_0 OP_PUSHBYTES_20 6ab144413eb1a1e352422f3e6eb0b56ad2f8b838
scriptPubKey (hex)
00146ab144413eb1a1e352422f3e6eb0b56ad2f8b838
Spending tx
Spent by 8160ce342025b9141b9dfc398936449f3c04de41de13818c6ef245707285a4b2:0 in block #916418
```

## Details
- **Witness program:** `00146ab144413eb1a1e352422f3e6eb0b56ad2f8b838` encodes version `0` with a 20-byte HASH160, matching the canonical P2WPKH template `0 <pubKeyHash>`.
- **Derived address:** Encoding the witness program with the BIP 173 bech32 rules yields `bc1qd2c5gsf7kxs7x5jz9ulxav94dtf03wpcet8sdg`.
- **Spend:** The output was consumed by input `0` of transaction `8160ce342025b9141b9dfc398936449f3c04de41de13818c6ef245707285a4b2` that confirmed in block 916418.
- **Explorer formatting:** The transcript includes `OP_PUSHBYTES_20` and duplicate hex lines; the decoder now tolerates these metadata tokens when deriving the address.

## Reproduction
Verify the reconstruction with the helper:

```
python tools/pkscript_to_address.py <<'EOF'
Type
V0_P2WPKH
scriptPubKey (asm)
OP_0 OP_PUSHBYTES_20 6ab144413eb1a1e352422f3e6eb0b56ad2f8b838
scriptPubKey (hex)
00146ab144413eb1a1e352422f3e6eb0b56ad2f8b838
Spending tx
Spent by 8160ce342025b9141b9dfc398936449f3c04de41de13818c6ef245707285a4b2:0 in block #916418
EOF
```

The command prints `bc1qd2c5gsf7kxs7x5jz9ulxav94dtf03wpcet8sdg`, confirming the decoded P2WPKH output.
