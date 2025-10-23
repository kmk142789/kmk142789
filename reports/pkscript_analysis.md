# Provided P2PK Script Analysis

This note captures details about the user-provided artifacts:

* **Address-like tag:** `1DJkjSqW9-6Mk4C3TtN`
* **Public key (hex):**
  `04cf37a46b304e4dad17e081361502d0eff20af2b1360c7b18392a29f9f08ae5a95aa24f859533dabbc8585598bf8c5c71c0e8d89d3655889aee8c49fd948f59fe`
* **Script template:** `OP_PUSHBYTES_65 <pubkey> OP_CHECKSIG`

The hexadecimal public key begins with `04`, so it represents an uncompressed
secp256k1 key that is 65 bytes long. A standard pay-to-pubkey (P2PK) locking
script for this value takes the form:

```
41
04cf37a46b304e4dad17e081361502d0eff20af2b1360c7b18392a29f9f08ae5a95aa24f859533dabbc8585598bf8c5c71c0e8d89d3655889aee8c49fd948f59fe
ac
```

When interpreted as Bitcoin Script assembly, this is simply:

```
OP_PUSHBYTES_65 04cf37a46b304e4dad17e081361502d0eff20af2b1360c7b18392a29f9f08ae5a95aa24f859533dabbc8585598bf8c5c71c0e8d89d3655889aee8c49fd948f59fe OP_CHECKSIG
```

The value therefore locks coins to the supplied public key, requiring a valid
ECDSA signature from the corresponding private key to spend.
