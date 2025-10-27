# PKScript Analysis: 1LrrNP28PYg1N1z5Uo1gR8cmoPc8h4orBZ

## Summary
The provided transcript is the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script. Restoring the elided Base58Check segment in the label `1LrrNP28P-Pc8h4orBZ` produces the full mainnet address `1LrrNP28PYg1N1z5Uo1gR8cmoPc8h4orBZ`.

```text
1LrrNP28P-Pc8h4orBZ
Pkscript
OP_DUP
OP_HASH160
d9d7fb9cf1d10075b0515591e2570c7efabc80c1
OP_EQUALVERIFY
OP_CHECKSIG
```

## Details
- **Script template:** The opcode sequence `OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG` is the textbook P2PKH form that locks an output to whoever can present a matching public key and signature.
- **Hash payload:** The 20-byte digest `d9d7fb9cf1d10075b0515591e2570c7efabc80c1` is interpreted as a HASH160 value. Prefixing it with the Bitcoin mainnet version byte (`0x00`), appending the four-byte checksum, and Base58Check encoding the result yields the address above.
- **Hyphenated clue:** The dash in `1LrrNP28P-Pc8h4orBZ` hides the middle Base58 run `Yg1N1z5Uo1gR8cmo`. Reinserting that substring reconstructs the canonical address printed in the summary.

## Reproduction
The repository helper confirms the reconstruction directly:

```bash
python tools/pkscript_to_address.py <<'EOF'
1LrrNP28P-Pc8h4orBZ
Pkscript
OP_DUP
OP_HASH160
d9d7fb9cf1d10075b0515591e2570c7efabc80c1
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running the command prints `1LrrNP28PYg1N1z5Uo1gR8cmoPc8h4orBZ`, validating the interpretation.
