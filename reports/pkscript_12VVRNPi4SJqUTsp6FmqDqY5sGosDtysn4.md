# PKScript Analysis: 12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4

## Summary
The supplied listing is a standard pay-to-public-key-hash (P2PKH) locking script. It duplicates the top stack item, hashes it with `OP_HASH160`, compares the result against the provided 20-byte hash, and finally executes `OP_CHECKSIG` (split across two lines in the submission) to require a signature corresponding to the original public key hash.

```
OP_DUP OP_HASH160 105b7f253f0ebd7843adaebbd805c944bfb863e4 OP_EQUALVERIFY OP_CHECKSIG
```

## Details
- **Hash target:** The 20-byte payload `105b7f253f0ebd7843adaebbd805c944bfb863e4` is the HASH160 digest that the redeeming public key must match. Re-encoding it with the Bitcoin mainnet prefix (`0x00`) and Base58Check encoding yields the address `12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4`.
- **Script structure:** The tokens follow the canonical P2PKH pattern (`OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG`). The original transcript split `OP_CHECKSIG` across two lines as `OP_CH` and `ECKSIG`; combining them restores the final opcode.
- **Label formatting:** The leading line `12VVRNPi4-GosDtysn4` omits the central portion of the Base58Check string and inserts a hyphen. Restoring the missing characters produces the address above, consistent with the decoded hash.

## Reproduction
The repository helper can be used to confirm the derivation:

```
python tools/pkscript_to_address.py <<'EOF'
12VVRNPi4-GosDtysn4
Pkscript
OP_DUP
OP_HASH160
105b7f253f0ebd7843adaebbd805c944bfb863e4
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

Running this command prints `12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4`, matching the interpretation above.
