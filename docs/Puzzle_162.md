# Bitcoin Puzzle #162 — Restoring the Broadcast Address

Puzzle #162 again publishes the classic pay-to-public-key-hash (P2PKH)
locking script, but the Base58Check address that accompanies the clue is
shown with its middle section excised:

```
17DTUTXUc-Lrs1xMnS2
Pkscript
OP_DUP
OP_HASH160
442bd85a46d4acd7b082c1d731fb13c8474ffa6f
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
473044022040d5ec7eb54900e560cac0912b5a08f339636a9cba2bf778a7ff8c780abae5220220263c238cfba6144c824307f3662827e2b3b620cbfabf0a0152ad7ba8de73eb8c012103294d33f5e7b98c885ff540fd3f747010999f640d8fdb021f5a13ef3d06c36a58
Witness
```

Once the opcodes are lined up, the template matches the legacy P2PKH
form exactly:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing Base58Check infix requires only the standard
address-derivation steps:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and take the first four checksum bytes.
3. Append the checksum and encode the 25-byte payload with the Bitcoin
   Base58 alphabet.

Carrying out the procedure reveals the hidden segment:

- **Address:** `17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2`
- **Missing segment:** `UYEgrr5GhivxYei4`

Re-encoding the address confirms that it hashes back to the provided
`442bd85a46d4acd7b082c1d731fb13c8474ffa6f` payload, validating the
canonical P2PKH locking script.

### Inspecting the spend metadata

The transcript also includes a complete unlocking script.  Parsing the
`Sigscript` entry reveals a 71-byte DER signature followed by a compressed
secp256k1 public key:

```python
import binascii
import hashlib

sigscript = binascii.unhexlify(
    "473044022040d5ec7eb54900e560cac0912b5a08f339636a9cba2bf778a7ff8c780abae522"
    "0220263c238cfba6144c824307f3662827e2b3b620cbfabf0a0152ad7ba8de73eb8c01"
    "2103294d33f5e7b98c885ff540fd3f747010999f640d8fdb021f5a13ef3d06c36a58"
)

sig_length = sigscript[0]
signature = sigscript[1 : 1 + sig_length]
sighash_flag = signature[-1]
compressed_pubkey = sigscript[1 + sig_length + 1 :]

print(len(signature[:-1]), sighash_flag)  # 70-byte DER signature, SIGHASH_ALL
print(compressed_pubkey.hex())

payload = hashlib.new("ripemd160", hashlib.sha256(compressed_pubkey).digest()).hexdigest()
print(payload)
```

Running the snippet prints the compressed key
`03294d33f5e7b98c885ff540fd3f747010999f640d8fdb021f5a13ef3d06c36a58` and the
hash `442bd85a46d4acd7b082c1d731fb13c8474ffa6f`, confirming that the spend
data matches the reconstructed locking script.

To reproduce the decoding with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """17DTUTXUc-Lrs1xMnS2\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "442bd85a46d4acd7b082c1d731fb13c8474ffa6f\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2`, confirming
the restored address for Bitcoin Puzzle #162.
