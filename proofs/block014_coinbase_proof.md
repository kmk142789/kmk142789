# Block 14 Coinbase Proof

This proof note captures the verification steps for Bitcoin block **#14**, adding another canonical coinbase reconstruction to the Satoshi-era mining dossier. Following the same recipe as prior entries ensures anyone can independently reproduce the witness data and recipient address.

## 1. Query the height endpoint and fetch the block

```bash
curl -s https://blockstream.info/api/block-height/14
curl -s https://blockstream.info/api/block/0000000080f17a0c5a67f663a9bc9969eb37e81666d9321125f0e293656f8a37/raw > block14.raw
```

The first command resolves the height to its canonical hash, and the second downloads the raw 215-byte block blob for local decoding.

## 2. Parse the coinbase transaction

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

raw = open('block14.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)
read_varint(stream)
stream.read(4)
read_varint(stream)
stream.read(32 + 4)
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)
read_varint(stream)
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

The decoder surfaces the precise witness string, subsidy, and destination:

```
scriptSig (base64): BP//AB0BPg==
coinbase value (sats): 5000000000
pk_script: 41043e8ac6b8ea64e85928b6469f17db0096de0bcae7d09a4497413d9bba49c00ffdf9cb0ce07c404784928b3976f0beea42fe2691a8f0430bcb2b0daaf5aa02b30eac
address: 1DMGtVnRrgZaji7C9noZS3a1QtoaAN2uRG
```

As expected, block #14 also awards 50 BTC to a single pay-to-pubkey output, providing another directly inspectable data point in the Satoshi controlled mining run.

## 3. Clean up

```bash
rm block14.raw
```

Deleting the downloaded raw file prevents stale binaries from accumulating between attestations.
