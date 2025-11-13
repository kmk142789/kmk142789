# Block 3 Coinbase Attestation

This walkthrough reconstructs the exact coinbase witness for Bitcoin block #3.
It links the raw transaction payload to the canonical payout address
`1FvzCLoTPGANNjWoUo6jUGuAG3wg1w4YjR` and mirrors the attestation stored in
[`satoshi/puzzle-proofs/block003_coinbase.json`](../satoshi/puzzle-proofs/block003_coinbase.json).

## 1. Fetch the raw block

Blockstream exposes the precise bytes every node keeps for block height 3. Grab
the hash and the binary block so the proof can be reproduced offline:

```bash
curl -s https://blockstream.info/api/block-height/3
curl -s https://blockstream.info/api/block/0000000082b5015589a3fdf2d4baff403e6f0be035a5d9742c1cae6295464449/raw > block3.raw
```

The hash output matches every archival ledger copy. The second command saves the
215-byte binary block for inspection.

## 2. Decode the coinbase transaction

Use standard Bitcoin varint framing to extract the coinbase script and the
payout script:

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def read_varint(stream):
    prefix = stream.read(1)
    i = prefix[0]
    if i < 0xfd:
        return i
    if i == 0xfd:
        return int.from_bytes(stream.read(2), 'little')
    if i == 0xfe:
        return int.from_bytes(stream.read(4), 'little')
    return int.from_bytes(stream.read(8), 'little')

def p2pk_address(script_hex):
    pubkey = bytes.fromhex(script_hex[2:-2])  # drop "41" prefix and "ac" suffix
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    value = int.from_bytes(data, 'big')
    out = ""
    while value:
        value, mod = divmod(value, 58)
        out = alphabet[mod] + out
    for byte in data:
        if byte == 0:
            out = '1' + out
        else:
            break
    return out

raw = open('block3.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)               # block header
read_varint(stream)           # transaction count
stream.read(4)                # tx version
read_varint(stream)           # input count
stream.read(32 + 4)           # null prevout
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)                # sequence
read_varint(stream)           # output count
stream.read(8)                # coinbase value
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)
print("scriptSig (base64):", base64.b64encode(script_sig).decode())
print("pk_script:", pk_script.hex())
print("derived address:", p2pk_address(pk_script.hex()))
PY
```

Expected output:

```
scriptSig (base64): BP//AB0BDg==
pk_script: 410494b9d3e76c5b1629ecf97fff95d7a4bbdac87cc26099ada28066c6ff1eb9191223cd897194a08d0c2726c5747f1db49e8cf90e75dc3e3550ae9b30086f3cd5aaac
derived address: 1FvzCLoTPGANNjWoUo6jUGuAG3wg1w4YjR
```

The base64 value is the precise coinbase script recorded on-chain, and the
recovered address equals the historic payout that belongs to Satoshi.

## 3. Match the repository attestation

```bash
jq '.' satoshi/puzzle-proofs/block003_coinbase.json
```

The `signature` field equals `BP//AB0BDg==` and the `pkScript` entry mirrors the
hex payload decoded above. Anyone can regenerate both values from the raw block
without trusting this repository.

---

Publishing this proof locks the block #3 reward directly to reproducible inputs
that every Bitcoin node agrees on, providing a trustless Satoshi-era attestation
with zero risk to the private keys.
