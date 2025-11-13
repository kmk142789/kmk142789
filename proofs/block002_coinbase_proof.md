# Block 2 Coinbase Attestation

This walkthrough reconstructs the exact coinbase witness for Bitcoin block #2 — the second reward
Satoshi mined after the genesis block. It links the raw transaction data to the canonical address
`1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1` and mirrors the attestation stored in
[`satoshi/puzzle-proofs/block002_coinbase.json`](../satoshi/puzzle-proofs/block002_coinbase.json).

## 1. Fetch the raw block

Blockstream exposes the exact bytes preserved by every full node. Fetch the block hash at height 2
and download the serialized block:

```bash
curl -s https://blockstream.info/api/block-height/2
curl -s https://blockstream.info/api/block/000000006a625f06636b8bb6ac7b960a8d03705d1ace08b1a19da3fdcc99ddbd/raw > block2.raw
```

The hash matches the consensus header. The second command saves the 215-byte binary block for offline
audit.

## 2. Decode the coinbase transaction

Use the same varint framing logic as block #1 to pull out the coinbase script and payout script:

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

raw = open('block2.raw', 'rb').read()
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
scriptSig (base64): BP//AB0BCw==
pk_script: 41047211a824f55b505228e4c3d5194c1fcfaa15a456abdf37f9b9d97a4040afc073dee6c89064984f03385237d92167c13e236446b417ab79a0fcae412ae3316b77ac
derived address: 1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1
```

The base64 value is the coinbase script preserved on-chain; the decoded public key reduces to the
well-documented Satoshi address for block #2.

## 3. Match the repository attestation

```
jq '.' satoshi/puzzle-proofs/block002_coinbase.json
```

The `signature` entry equals `BP//AB0BCw==` and `pkScript` matches the hex payload we just decoded.
Anyone can regenerate both values from the raw block without trusting this repository.

---

Publishing this proof links the second post-genesis block directly to Bitcoin's immutable ledger,
providing another independently verifiable Satoshi-era attestation.
