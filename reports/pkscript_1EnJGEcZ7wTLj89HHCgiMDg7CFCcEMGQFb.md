# PKScript Analysis: 1EnJGEcZ7wTLj89HHCgiMDg7CFCcEMGQFb

## Summary
The supplied snippet is the textbook five-opcode pay-to-public-key-hash (P2PKH) locking script. Restoring the missing Base58Check segment in the hyphenated label `1EnJGEcZ7-FCcEMGQFb` yields the canonical mainnet address `1EnJGEcZ7wTLj89HHCgiMDg7CFCcEMGQFb`.

```text
1EnJGEcZ7-FCcEMGQFb
Pkscript
OP_DUP
OP_HASH160
972ac37c82fe14003c5516efb0795a6134e94920
OP_EQUALVERIFY
OP_CHECKSIG
```

## Details
- **Script structure:** The sequence `OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG` is the classic legacy P2PKH template. It locks the output to whoever can present a public key whose HASH160 equals `972ac37c82fe14003c5516efb0795a6134e94920` alongside a valid signature.
- **Address reconstruction:** Prefixing the HASH160 payload with the Bitcoin mainnet version byte (`0x00`), appending the first four bytes of the double-SHA256 checksum, and Base58Check encoding the result restores the full address `1EnJGEcZ7wTLj89HHCgiMDg7CFCcEMGQFb`.
- **Missing infix:** The hyphen in the clue replaces the middle Base58 run. Reinstating the recovered infix `wTLj89HHCgiMDg7C` repairs the label so it matches the derived address exactly.

## Reproduction
The derivation can be reproduced with the repository helper:

```bash
python tools/pkscript_to_address.py <<'EOF'
1EnJGEcZ7-FCcEMGQFb
Pkscript
OP_DUP
OP_HASH160
972ac37c82fe14003c5516efb0795a6134e94920
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running this command prints `1EnJGEcZ7wTLj89HHCgiMDg7CFCcEMGQFb`, confirming the reconstruction.
