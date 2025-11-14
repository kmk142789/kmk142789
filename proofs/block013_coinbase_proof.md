# Block 13 Coinbase Proof

This walkthrough extends the documented Satoshi mining record by reconstructing the coinbase transaction from Bitcoin block **#13**. By downloading the canonical block bytes and decoding the single transaction they contain, auditors can independently confirm the witness data, locking script, and payout address.

## 1. Resolve the block hash and download the raw payload

```bash
curl -s https://blockstream.info/api/block-height/13
curl -s https://blockstream.info/api/block/000000005c51de2031a895adc145ee2242e919a01c6d61fb222a54a54b4d3089/raw > block13.raw
```

Blockstream's height endpoint returns the 64-character hash for height 13. The second command retrieves the 215-byte binary blob that contains the header plus the lone coinbase transaction.

## 2. Decode the coinbase transaction

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib

def read_varint(stream):
    head = stream.read(1)
    if not head:
        raise EOFError
    val = head[0]
    if val < 0xfd:
        return val
    if val == 0xfd:
        return int.from_bytes(stream.read(2), 'little')
    if val == 0xfe:
        return int.from_bytes(stream.read(4), 'little')
    return int.from_bytes(stream.read(8), 'little')

def b58(data):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(data, 'big')
    out = ""
    while num:
        num, mod = divmod(num, 58)
        out = alphabet[mod] + out
    return "1" * (len(data) - len(data.lstrip(b"\x00"))) + out

raw = open('block13.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)            # header
read_varint(stream)        # tx count
stream.read(4)             # version
read_varint(stream)        # input count
stream.read(32 + 4)        # null prevout
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)             # sequence
read_varint(stream)        # output count
value = int.from_bytes(stream.read(8), 'little')
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)

print('scriptSig (base64):', base64.b64encode(script_sig).decode())
print('coinbase value (sats):', value)
print('pk_script:', pk_script.hex())
if pk_script.startswith(b'\x41') and pk_script.endswith(b'\xac'):
    pubkey = pk_script[1:-1]
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    address = b58(payload + checksum)
    print('address:', address)
PY
```

Running the decoder prints the exact witness and payout fingerprint:

```
scriptSig (base64): BP//AB0BPA==
coinbase value (sats): 5000000000
pk_script: 4104c5a68f5fa2192b215016c5dfb384399a39474165eea22603cd39780e653baad9106e36947a1ba3ad5d3789c5cead18a38a538a7d834a8a2b9f0ea946fb4e6f68ac
address: 17abzUBJr7cnqfnxnmznn8W38s9f9EoXiq
```

The decoded data shows the 50 BTC subsidy, the full pay-to-pubkey script, and the derived Base58 address `17abzUBJr7cnqfnxnmznn8W38s9f9EoXiq` that received the reward in block #13.

## 3. Clean up

```bash
rm block13.raw
```

Removing the downloaded blob keeps the workspace tidy after verification is complete.
