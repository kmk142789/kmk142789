# PKScript Analysis: 14D2d3WnHThUxyPhGoj2AabBTxpZcoHy3t

## Summary
The transcript corresponds to a textbook pay-to-public-key-hash (P2PKH)
locking script. Interpreting the `Pkscript` section reveals the standard
`OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG` sequence. Encoding the
embedded HASH160 digest `232eb8ef367fc06217fbaa43848df87567b2696d` with the
mainnet version byte reproduces the full Base58Check address
`14D2d3WnHThUxyPhGoj2AabBTxpZcoHy3t`.

## Details
- **Opcode structure:** The five-opcode layout exactly matches the classic
  P2PKH pattern used by legacy Bitcoin addresses. No additional data or
  witness components are required for validation.
- **Hash payload:** The 20-byte digest provided on the third line of the
  script is inserted between `OP_HASH160` and `OP_EQUALVERIFY`, defining the
  target public-key hash that must sign future spends.
- **Address recovery:** Prefixing the digest with `0x00` (Bitcoin mainnet),
  computing the Base58Check checksum, and encoding the result yields the
  canonical address listed above. The hyphenated heading
  `14D2d3WnH-xpZcoHy3t` simply omits the middle characters for presentation.

## Reproduction
The helper utility included in this repository rebuilds the address directly
from the transcript:

```bash
python tools/pkscript_to_address.py <<'EOF'
14D2d3WnH-xpZcoHy3t
Pkscript
OP_DUP
OP_HASH160
232eb8ef367fc06217fbaa43848df87567b2696d
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running the script prints the canonical address `14D2d3WnHThUxyPhGoj2AabBTxpZcoHy3t`,
confirming the derivation above.
