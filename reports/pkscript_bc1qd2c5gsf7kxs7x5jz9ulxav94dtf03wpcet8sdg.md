# PKScript Analysis: bc1qd2c5gsf7kxs7x5jz9ulxav94dtf03wpcet8sdg

## Summary
The provided locking script is a SegWit pay-to-witness-public-key-hash (P2WPKH) output. It uses witness version `0` (`OP_0`) followed by a 20-byte HASH160. Funds locked to this script can be spent by supplying a compressed secp256k1 public key whose HASH160 matches the witness program and an ECDSA signature in the witness stack.

```
00146ab144413eb1a1e352422f3e6eb0b56ad2f8b838
```

## Details
- **Witness program structure:** `OP_0` plus a 20-byte push fits the canonical SegWit v0 template `0 <pubKeyHash>` used by P2WPKH outputs.
- **Derived address:** Encoding the script with BIP-0173 bech32 produces `bc1qd2c5gsf7kxs7x5jz9ulxav94dtf03wpcet8sdg`, matching the supplied previous-output address.
- **Witness stack:** The witness contains a DER-encoded signature ending in `0x01`, signalling `SIGHASH_ALL`, and a 33-byte compressed public key beginning with `0x02`. Hashing that key with SHA-256 and RIPEMD-160 yields `6ab144413eb1a1e352422f3e6eb0b56ad2f8b838`, exactly reproducing the witness program above.
- **nSequence:** The input used `0xffffffff`, the default final sequence number, so no relative timelock features are engaged.

```
Witness
30440220384b0784d012f2af2bb4c6e33823adb9e888566c2039e4e1733f117920a4ab4c02200237a6dd8be4eba82a2f0df12f4ec192d12f64e1c7c99b1ea2108970fb1209fe01
02eb7a61f5fb650d7939e6508ceacb30342b138428dfb2a1ff9482a3b614ef0d26
nSequence
0xffffffff
```

## Reproduction
The bech32 address can be regenerated with the repository helper:

```
python tools/pkscript_to_address.py <<'EOF'
Pkscript
00146ab144413eb1a1e352422f3e6eb0b56ad2f8b838
EOF
```

This prints `bc1qd2c5gsf7kxs7x5jz9ulxav94dtf03wpcet8sdg`, confirming the decoding above.
