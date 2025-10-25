# Bitcoin Puzzle #17 — Restoring the Broadcast P2PKH Address

Puzzle #17 advertises the familiar five-opcode pay-to-public-key-hash (P2PKH) locking script, but the Base58Check
address is published with its midpoint suppressed:

```
1HduPEXZR-yjnZuJ7Bm
Pkscript
OP_DUP
OP_HASH160
b67cb6edeabc0c8b927c9ea327628e7aa63e2d52
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode layout already matches the canonical P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

All that remains is to rebuild the missing Base58Check run. Following the textbook procedure:

1. Prepend the mainnet version byte `0x00` to the 20-byte HASH160 payload.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four bytes.
3. Encode the resulting 25-byte buffer using the Bitcoin Base58 alphabet.

Executing these steps restores the elided centre and yields the full destination:

- **Address:** `1HduPEXZRdG26SUT5Yk83mLkPyjnZuJ7Bm`
- **Missing segment:** `dG26SUT5Yk83mLkP`

The reconstructed address agrees with the authoritative entry in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which associates HASH160
`b67cb6edeabc0c8b927c9ea327628e7aa63e2d52` with the same Puzzle #17 mainnet address.

To confirm the derivation with the local tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1HduPEXZR-yjnZuJ7Bm\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "b67cb6edeabc0c8b927c9ea327628e7aa63e2d52\nOP_EQUALVERIFY\nOP_CHECKSIG"

decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1HduPEXZRdG26SUT5Yk83mLkPyjnZuJ7Bm`, confirming the repaired address for Bitcoin Puzzle #17.
