# Block 11 Proof-of-Work Verification

This proof reproduces the SHA256d hash for block **11** and compares it against the target encoded in its `nBits` field. Everything
 happens with only the raw block payload pulled from Blockstream.

## 1. Download the raw block (reuse if already present)

```bash
curl -s https://blockstream.info/api/block/0000000097be56d606cdd9c54b04d4747e957d3608abe69198c661f2add73073/raw > block11.raw
```

## 2. Recompute the block hash and target check

```bash
python - <<'PY'
import hashlib, struct
raw = open('block11.raw', 'rb').read()
header = raw[:80]
double_hash = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
print('computed hash:', double_hash)
expected = '0000000097be56d606cdd9c54b04d4747e957d3608abe69198c661f2add73073'
print('matches block explorer hash?', double_hash == expected)
# parse nBits and derive integer target
bits = struct.unpack('<I', header[72:76])[0]
exp = bits >> 24
mant = bits & 0xffffff
target = mant * (1 << (8 * (exp - 3)))
value = int(double_hash, 16)
print('nBits:', hex(bits))
print('target:', target)
print('hash value:', value)
print('meets target?', value <= target)
PY
```

Expected output:

```
computed hash: 0000000097be56d606cdd9c54b04d4747e957d3608abe69198c661f2add73073
matches block explorer hash? True
nBits: 0x1d00ffff
target: 26959535291011309493156476344723991336010898738574164086137773096960
hash value: 15980457048563306273024894396149705010776030229048116624968711090291
meets target? True
```

Because the SHA256d digest is strictly smaller than the target encoded by `0x1d00ffff`, the block header undeniably satisfies
 Bitcoin's proof-of-work requirement for height 11. Any alternative history would have to reproduce a header whose double hash is
 at most the same target, which makes this proof tamper evident.
