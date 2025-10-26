# PKScript Analysis: 1FQtCEEEiLuFTvhbx4Z5fda3GXV5xXzmfN

## Summary
The transcript encodes a standard pay-to-public-key-hash (P2PKH) locking
script. Decoding the hexadecimal `Pkscript` line reveals the textbook five
opcode sequence `OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG`. Once the
embedded HASH160 payload is Base58Check encoded with the mainnet version byte,
it yields the full address `1FQtCEEEiLuFTvhbx4Z5fda3GXV5xXzmfN`.

## Details
- **Hash target:** Parsing `76a9149e160ff616c4b03650ae590677898c9b00c3100088ac`
  produces the conventional P2PKH pattern with HASH160 payload
  `9e160ff616c4b03650ae590677898c9b00c31000`. Prefixing the payload with
  `0x00` and applying Base58Check encoding restores the complete Base58 address
  above.
- **Label formatting:** The heading `1FQtCEEEi-XV5xXzmfN` replaces the middle
  section of the address with a dash. Restoring the elided characters yields the
  canonical string shown in the summary.
- **Spend metadata:** The `Sigscript` block supplies a DER-encoded signature and
  a 65-byte uncompressed public key (prefix `0x04`). This data belongs to the
  spending transaction and does not affect the derived locking address. The
  empty `Witness` section is expected for a legacy P2PKH spend.

## Reproduction
The helper script trims trailing signature metadata, so the original transcript
can be decoded directly:

```bash
python tools/pkscript_to_address.py <<'EOF'
1FQtCEEEi-XV5xXzmfN
Pkscript
76a9149e160ff616c4b03650ae590677898c9b00c3100088ac
Sigscript
4830450220669c3e86bcaabb74cca59e1d5ee0f60f1698bb60a13aaa3971cfe8ef9119720b02210094e4d6f5c2a29ce3875e7b7786626e53ab94e4ffc0bde0dfc5daf1aa7574796e0141040147fd5cabcdea6c2ce0406cc9b746c565060f387b4c0b602fe36a991ab621a7523d889cdafc6ba6534a9f30e48334f528ae899ad6d65fce17d1ca65be2f2ce0
Witness
