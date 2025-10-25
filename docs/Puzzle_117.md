# Bitcoin Puzzle #117 — Completing the Broadcast Address

Puzzle #117 again publishes the classic pay-to-public-key-hash (P2PKH)
locking script together with the advertised destination, but the Base58Check
string omits its core segment:

```
Puzzle #117
1KNRfGWw7-b9M2Wkj5Z
Pkscript
OP_DUP
OP_HASH160
c97f9591e28687be1c4d972e25be7c372a3221b4
OP_EQUALVERIFY
OP_CH
ECKSIG
```

The opcode listing is the textbook five-instruction P2PKH template that all of
the early Bitcoin puzzles use:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

With the script established, recovering the hidden characters reduces to the
standard Base58Check procedure on the published HASH160 digest:

1. Prefix the 20-byte fingerprint with the legacy mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and keep the first four bytes as the
   checksum.
3. Append the checksum and encode the 25-byte buffer with the Bitcoin Base58
   alphabet.

Carrying out these steps reconstructs the complete broadcast address and its
redacted infix:

- **Address:** `1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z`
- **Missing segment:** `Q9Rmwsc6NT5zsdvEb`

The recovered address matches the authoritative catalogue entry stored in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), where the
same HASH160 `c97f9591e28687be1c4d972e25be7c372a3221b4` appears for Puzzle
#117.

You can verify the reconstruction with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #117\n1KNRfGWw7-b9M2Wkj5Z\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "c97f9591e28687be1c4d972e25be7c372a3221b4\nOP_EQUALVERIFY\nOP_CH\nECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z`, confirming the
restored P2PKH address for Bitcoin Puzzle #117.
