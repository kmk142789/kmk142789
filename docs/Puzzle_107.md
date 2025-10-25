# Bitcoin Puzzle #107 — Reassembling the Broadcast Address

Puzzle #107 once again publishes the canonical pay-to-public-key-hash (P2PKH)
locking script together with a Base58Check address whose middle segment has
been redacted:

```
15EJFC5ZT-Yq3SWaxTc
Pkscript
OP_DUP
OP_HASH160
2e644e46b042ffa86da35c54d7275f1abe6d4911
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence matches the standard P2PKH template that appears
throughout the Bitcoin puzzle series. With the HASH160 fingerprint supplied,
recovering the missing characters is a straightforward Base58Check encoding
exercise:

1. Prefix the 20-byte hash with the mainnet version byte `0x00`.
2. Compute the checksum by double-SHA256 hashing the 21-byte payload and
   keeping the first four bytes.
3. Append the checksum and encode the 25-byte buffer with Bitcoin's Base58
   alphabet.

Executing these steps restores the censored infix and yields the full legacy
address:

- **Address:** `15EJFC5ZTs9nhsdvSUeBXjLAuYq3SWaxTc`
- **Missing segment:** `s9nhsdvSUeBXjLAu`

The reconstructed address aligns with the authoritative catalogue entry stored
in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which
records the same HASH160 `2e644e46b042ffa86da35c54d7275f1abe6d4911` for Puzzle
#107.

You can verify the reconstruction with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #107\n15EJFC5ZT-Yq3SWaxTc\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "2e644e46b042ffa86da35c54d7275f1abe6d4911\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `15EJFC5ZTs9nhsdvSUeBXjLAuYq3SWaxTc`, confirming the
restored P2PKH address for Bitcoin Puzzle #107.
