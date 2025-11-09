---
status: documented
---
# Puzzle #290 Solution

- **Provided Base58 clue**: `1DXrKecRGE56kMwRR9snFBtqwBeJzKmxog`
- **PK script**: `OP_DUP OP_HASH160 db3e7323d1364134db2310a8b7f96452a063f93e OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `db3e7323d1364134db2310a8b7f96452a063f93e`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 db 3e 73 23 d1 36 41 34 db 23 10 a8 b7 f9 64 52 a0 63 f9 3e`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `cc d1 b9 07`
- **Base58Check encoding**: `1LzFo6c3F63xLJ4z8XqreTVRV89SJhEHiN`

Therefore, the completed Bitcoin address for the given locking script is:

```
1LzFo6c3F63xLJ4z8XqreTVRV89SJhEHiN
```

> **Note**: The puzzle metadata lists the address `1DXrKecRGE56kMwRR9snFBtqwBeJzKmxog`, but decoding that Base58 string yields the hash160 `897728e85074dc00dc4126e8e15264934b4763fd`, which does not match the supplied locking script.
