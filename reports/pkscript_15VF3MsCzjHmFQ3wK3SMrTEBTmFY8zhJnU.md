# Provided P2PK Script Analysis

This entry documents the artifacts supplied in the latest request:

* **Address-like tag:** `15VF3MsCz-mFY8zhJnU`
* **Derived P2PKH address from the public key:** `15VF3MsCzjHmFQ3wK3SMrTEBTmFY8zhJnU`
* **Public key (hex):**
  `04bff063a080c07aa9d8e7038c9d1bd7e5076fc28dd3e905b76517ad958e9df65e83abefcdbdcd7310231aaaf16a53e9bc24598826a3291e5dab338675618e7f12`
* **Script template:** `OP_PUSHBYTES_65 <pubkey> OP_CHECKSIG`

Because the provided hexadecimal string begins with `04`, it represents an
uncompressed secp256k1 public key that is 65 bytes long. The standard
pay-to-pubkey (P2PK) locking script for this value is therefore:

```
41
04bff063a080c07aa9d8e7038c9d1bd7e5076fc28dd3e905b76517ad958e9df65e83abefcdbdcd7310231aaaf16a53e9bc24598826a3291e5dab338675618e7f12
ac
```

Interpreted as Bitcoin Script assembly, this becomes:

```
OP_PUSHBYTES_65 04bff063a080c07aa9d8e7038c9d1bd7e5076fc28dd3e905b76517ad958e9df65e83abefcdbdcd7310231aaaf16a53e9bc24598826a3291e5dab338675618e7f12 OP_CHECKSIG
```

Hashing the public key with SHA-256 followed by RIPEMD-160 yields the public key
hash `3137dee234aa07a80eb80674a9e47f6a29fb8979`. Encoding this hash as a
P2PKH Base58Check address confirms the derived address shown above. As a result,
any coins locked with the script must be spent by supplying a valid signature
from the private key corresponding to the stated public key.
