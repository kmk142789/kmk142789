# PKScript Analysis: 1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D

## Summary
The transcript corresponds to the standard pay-to-public-key-hash (P2PKH) locking script. It duplicates the supplied public key, hashes it with `OP_HASH160`, compares the result to the embedded 20-byte digest, and finishes with `OP_CHECKSIG`—split across the `OP_CH` / `ECKSIG` lines in the submission—to require a matching ECDSA signature.

```
OP_DUP OP_HASH160 7c99ce73e19f9fbfcce4825ae88261e2b0b0b040 OP_EQUALVERIFY OP_CHECKSIG
```

## Details
- **Hash target:** The 20-byte payload `7c99ce73e19f9fbfcce4825ae88261e2b0b0b040` re-encodes with the Bitcoin mainnet prefix (`0x00`) to the Base58Check address `1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D`.
- **Script structure:** The opcode sequence matches the canonical P2PKH template (`OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG`). Normalising the fragmented `OP_CH` / `ECKSIG` tokens restores the terminal opcode without altering semantics.
- **Metadata lines:** The opening `Number #84` banner is descriptive text; the decoder skips it when extracting the five-token P2PKH sequence.
- **Label formatting:** The leading `1CMq3SvFc-sK1oicG2D` label inserts a hyphen and drops the central characters of the Base58Check string. Removing the punctuation and reinstating the missing portion yields the full address derived above.

## Reproduction
The repository helper can be used to verify the interpretation:

```
python tools/pkscript_to_address.py <<'EOF'
1CMq3SvFc-sK1oicG2D
Pkscript
OP_DUP
OP_HASH160
7c99ce73e19f9fbfcce4825ae88261e2b0b0b040
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

Executing this command prints `1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D`, confirming the decoded address.

