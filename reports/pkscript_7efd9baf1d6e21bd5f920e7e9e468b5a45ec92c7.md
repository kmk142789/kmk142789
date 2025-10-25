# Puzzle #252 P2PKH Reconstruction

Puzzle #252 advertises the standard five-opcode pay-to-public-key-hash (P2PKH)
locking script with the trailing opcode split across two lines and the
associated Base58Check address partially redacted:

- Partial address: `1CaTxB3Yw-Rqs48xmui`
- HASH160 digest: `7efd9baf1d6e21bd5f920e7e9e468b5a45ec92c7`

The script follows the canonical P2PKH template:

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Encoding the 20-byte hash with the Bitcoin mainnet version byte (`0x00`) and
Base58Check checksum restores the missing section of the address.

## Address recovery

The helper under `tools/pkscript_to_address.py` can reconstruct the full
address directly from the published transcript:

```
python tools/pkscript_to_address.py <<'EOF_SNIPPET'
1CaTxB3Yw-Rqs48xmui
Pkscript
OP_DUP
OP_HASH160
7efd9baf1d6e21bd5f920e7e9e468b5a45ec92c7
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF_SNIPPET
```

Running the command prints `1CaTxB3YwmXZkDnTK4rRvq61SRqs48xmui`. The recovered
substring (`mXZkDnTK4rRvq61S`) matches the address derived from the HASH160
fingerprint via Base58Check encoding, confirming the interpretation of the
Puzzle #252 locking script.
