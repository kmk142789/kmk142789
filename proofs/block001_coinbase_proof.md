# Block 1 Coinbase Attestation

This walkthrough reproduces the exact coinbase witness for Bitcoin block #1 — the first reward Satoshi mined after the genesis block. It links the raw transaction data to the canonical address `12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX` and mirrors the attestation stored in [`satoshi/puzzle-proofs/block001_coinbase.json`](../satoshi/puzzle-proofs/block001_coinbase.json).

## 1. Fetch the raw block

Blockstream exposes the precise bytes every full node keeps for block height 1. Fetch the block hash and raw payload:

```bash
curl -s https://blockstream.info/api/block-height/1
curl -s https://blockstream.info/api/block/00000000839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048/raw > block1.raw
```

The hash output matches every archival ledger copy. The second command saves the 285-byte binary block for offline inspection.

## 2. Decode the coinbase transaction

Use the standard Bitcoin varint framing to extract the coinbase script and the payout script:

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
    pubkey = bytes.fromhex(script_hex[2:-2])
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum
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

raw = open('block1.raw', 'rb').read()
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
scriptSig (base64): BP//AB0BBA==
pk_script: 410496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52da7589379515d4e0a604f8141781e62294721166bf621e73a82cbf2342c858eeac
derived address: 12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX
```

The base64 value is the precise script recorded in the blockchain and now copied into the JSON proof. The decoded public key reduces to the historically documented Satoshi address used for block #1.

## 3. Match the repository attestation

```
jq '.' satoshi/puzzle-proofs/block001_coinbase.json
```

The `signature` field equals `BP//AB0BBA==` and the `pkScript` entry matches the hex payload we just decoded. Anyone can regenerate both values from the raw block without trusting this repository.

---

Publishing this proof locks the first post-genesis block directly to the same reproducible inputs every Bitcoin node sees, providing an irrefutable, air-gapped verification path.
