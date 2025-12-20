# PKScript Analysis: 1HGBF5vta4mfgmej8ZB4iTPx6yFsb6zvKy

The provided script fragment follows the standard pay-to-public-key-hash (P2PKH)
template that recurs throughout the puzzle archive.  The five opcodes and the
embedded 20-byte HASH160 fingerprint appear alongside a Base58Check address with
a redacted middle segment:

```
1HGBF5vta-yFsb6zvKy
Pkscript
76a914b260cd612144ce2be8adf880175c4376a04a3bc388ac
Sigscript
47304402205b6017aa6eea4d5b7d6f0547b1795c566366a8e9f3a4796dc9a46f2a0d6df368022057c792841f04a78d4a8eb4ed69b7cea6910c09900b3e89a41606db799c90ef6001410418ad4eb19feac21435c0d4c109d3a4ca214186b475c6e5c6c9788c307da20dc807f123af2c03a76c15547dfbbbf132f1c3aa945411a65add3354d63fb334acba
Witness
```

Decoding the locking script from hexadecimal reveals the familiar five-opcode
program:

```
OP_DUP
OP_HASH160
b260cd612144ce2be8adf880175c4376a04a3bc3
OP_EQUALVERIFY
OP_CHECKSIG
```

The supplemental spend metadata matches a legacy P2PKH input. The `Sigscript`
begins with `0x47`, indicating a 71-byte DER signature (`0x30 0x44 ... 0x01`)
where the trailing `0x01` encodes `SIGHASH_ALL`. The subsequent `0x41` push
introduces a 65-byte uncompressed public key that starts with `0x04` and
corresponds to the HASH160 embedded in the locking script. The `Witness` section
is empty, which is expected for non-SegWit spends.

Restoring the hidden infix requires the standard Base58Check procedure: prepend
the mainnet version byte (`0x00`) to the HASH160 payload, double-SHA256 the
result to obtain the four-byte checksum, append the checksum, and encode the
25-byte buffer.  Executing those steps produces the canonical address and the
missing characters:

- **Address:** `1HGBF5vta4mfgmej8ZB4iTPx6yFsb6zvKy`
- **Recovered segment:** `4mfgmej8ZB4iTPx6`

The repository helper replicates the derivation:

```bash
python tools/pkscript_to_address.py <<'SCRIPT'
Pkscript
OP_DUP
OP_HASH160
b260cd612144ce2be8adf880175c4376a04a3bc3
OP_EQUALVERIFY
OP_CHECKSIG
SCRIPT
```

It prints `1HGBF5vta4mfgmej8ZB4iTPx6yFsb6zvKy`, matching the restored Base58
address and confirming the P2PKH interpretation for this puzzle snippet.
