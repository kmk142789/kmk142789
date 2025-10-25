# Pay-to-PubKey-Hash Script for 1A1zP1eP5

The Bitcoin genesis coinbase address `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` is locked by
the standard pay-to-pubkey-hash (P2PKH) script shown below:

```
OP_DUP
OP_HASH160
0x62e907b15cbf27d5425399ebf6f0fb50ebb88f18
OP_EQUALVERIFY
OP_CHECKSIG
```

## Field breakdown

| Bytecode | Meaning |
| --- | --- |
| `0x76` (`OP_DUP`) | Duplicate the top stack item so the supplied public key can be inspected twice. |
| `0xa9` (`OP_HASH160`) | Hash the duplicated public key with SHA-256 followed by RIPEMD-160. |
| `0x14` | Push the 20-byte public-key hash associated with the genesis output. |
| `62e907b15cbf27d5425399ebf6f0fb50ebb88f18` | The HASH160 fingerprint of the expected public key. |
| `0x88` (`OP_EQUALVERIFY`) | Abort unless the provided public key hashes to the expected value. |
| `0xac` (`OP_CHECKSIG`) | Verify that the provided signature matches the supplied public key. |

## Notes

* This script spends the reward from Block 0 (the Bitcoin genesis block). Any
  valid spend must supply a signature and public key whose hash is
  `62e907b15cbf27d5425399ebf6f0fb50ebb88f18`.
* Original transcripts of the script sometimes omit the `0x` prefix on the hash
  or split `OP_CHECKSIG` across two lines. The canonical assembly keeps
  `OP_CHECKSIG` as a single opcode token.
