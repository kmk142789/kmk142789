# PKScript Analysis: bc1qtrkzhyyxqhs49esfmqm8rhkwgr5kc6phu4dfsv

## Summary
The supplied locking script is a SegWit v0 pay-to-witness-public-key-hash (P2WPKH) output. Encoding the 20-byte witness program `58ec2b908605e152e609d83671dece40e96c6837` with BIP-0173 bech32 reproduces the address `bc1qtrkzhyyxqhs49esfmqm8rhkwgr5kc6phu4dfsv`.

```
Type
V0_P2WPKH
scriptPubKey (asm)
OP_0 OP_PUSHBYTES_20 58ec2b908605e152e609d83671dece40e96c6837
scriptPubKey (hex)
001458ec2b908605e152e609d83671dece40e96c6837
Spending tx
Spent by b20f39d352624cdf207199897e61edee906b0fa8e88bea5d1d8c56cd7f1a7f39:0 in block #917884
```

## Details
- **Witness program:** The segwit script begins with `OP_0` followed by a 20-byte push. Converting the hexadecimal payload `58ec2b908605e152e609d83671dece40e96c6837` back to bytes yields the HASH160 fingerprint of the controlling compressed public key.
- **Derived address:** BIP-0173 bech32 encoding of the program (with the mainnet HRP `bc`) returns the canonical P2WPKH address `bc1qtrkzhyyxqhs49esfmqm8rhkwgr5kc6phu4dfsv`.
- **Spending transaction:** The outpoint was consumed by input 0 of transaction `b20f39d352624cdf207199897e61edee906b0fa8e88bea5d1d8c56cd7f1a7f39`, which confirmed in block 917,884.

## Reproduction
Recreate the bech32 address directly from the script with the repository decoder:

```
python tools/decode_pkscript.py "OP_0 58ec2b908605e152e609d83671dece40e96c6837"
```

The script prints `bc1qtrkzhyyxqhs49esfmqm8rhkwgr5kc6phu4dfsv`, matching the derived SegWit address.
