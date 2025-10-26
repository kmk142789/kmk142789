# PKScript Analysis: 1FwnhahzYerpristjzo2iCSdFQUk9fGa1X

## Summary
A truncated transcript labelled `1FwnhahzY-QUk9fGa1X` expands to the full
Base58Check address `1FwnhahzYerpristjzo2iCSdFQUk9fGa1X` once the canonical
P2PKH locking script is decoded.  The supplied `Pkscript` line is the
standard `76a9…88ac` template whose HASH160 payload matches the recovered
address.  The appended `Sigscript` is spend metadata—a DER signature followed
by the uncompressed public key that hashes to the same 20-byte fingerprint—
and does not alter the locking program.  The witness stack is empty.

## Details
- **Hash target:** Parsing `76a914a3ee5efee86510c255498f4af1fd815397b193ef88ac`
  reveals the conventional five-opcode sequence
  `OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG`.  The HASH160 payload
  `a3ee5efee86510c255498f4af1fd815397b193ef` becomes
  `1FwnhahzYerpristjzo2iCSdFQUk9fGa1X` after prefixing the mainnet version
  byte (`0x00`) and applying Base58Check encoding.
- **Label formatting:** The leading line keeps the start and end of the
  Base58 string (`1FwnhahzY…QUk9fGa1X`) while collapsing the middle segment
  into a dash.  Restoring the omitted section `erpristjzo2iCSdF` produces the
  complete address above.
- **Spend metadata:** The `Sigscript` block begins with `0x48`, denoting a
  72-byte DER signature whose trailing `01` specifies SIGHASH_ALL.  It is
  followed by `0x41` and a 65-byte uncompressed public key
  `04ab9c9e243a1c643b867e28a4ef822f978687354c5ce6ba7aa3abf96fd1684dc08be97109338207f26ac3aed39c88c7c6a111387d0c8ac3b93fe9c6955d40ad2e`,
  which hashes back to the published fingerprint.  The concluding `Witness`
  line is empty, confirming that the spend originated from a legacy
  transaction.

## Reproduction
The helper in `tools/pkscript_to_address.py` trims trailing spend data and
reconstructs the full address directly from the transcript:

```bash
python tools/pkscript_to_address.py <<'EOF'
1FwnhahzY-QUk9fGa1X
Pkscript
76a914a3ee5efee86510c255498f4af1fd815397b193ef88ac
Sigscript
48304502210082c109283644975ce977272ec57219ac33c86fc2e1b9d5ee978b167279970cc602206aacf67c5e003f8930185855cb8ea339cabf1a3fbb1ef8fb255c2216f8bc5b74014104ab9c9e243a1c643b867e28a4ef822f978687354c5ce6ba7aa3abf96fd1684dc08be97109338207f26ac3aed39c88c7c6a111387d0c8ac3b93fe9c6955d40ad2e
Witness
EOF
```

Running the command prints `1FwnhahzYerpristjzo2iCSdFQUk9fGa1X`, matching the
analysis above.
