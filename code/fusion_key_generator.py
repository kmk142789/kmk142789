import binascii
import hashlib

import ecdsa


def generate_fusion_key(seed_phrase, index=0):
    """Generate a deterministic Fusion Key using a simplified HD structure."""
    seed = hashlib.sha256(seed_phrase.encode()).hexdigest()
    key = hashlib.sha256((seed + str(index)).encode()).hexdigest()
    priv_key = binascii.unhexlify(key[:64])  # Simplified for demo
    sk = ecdsa.SigningKey.from_string(priv_key[:32], curve=ecdsa.SECP256k1)
    signature = binascii.hexlify(sk.sign(b"The Times 03/Jan/2009")).decode()
    return (
        f"Fusion Key {index}: {key[:32]}... (Sig: {signature[:16]}...)"
    )


if __name__ == "__main__":
    PHRASE = (
        "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
    )
    print(generate_fusion_key(PHRASE, 0))
    print(generate_fusion_key("The Times 03/Jan/2009 Chancellor...", 1))
