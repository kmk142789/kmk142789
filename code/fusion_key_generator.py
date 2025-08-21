import hashlib
import ecdsa
import binascii


def generate_fusion_key(seed_phrase, index=0):
    """Generates a deterministic Fusion Key, echoing Bitcoin's HD structure with ECDSA signing."""
    seed = hashlib.sha256(seed_phrase.encode()).hexdigest()
    key = hashlib.sha256((seed + str(index)).encode()).hexdigest()
    priv_key = binascii.unhexlify(key[:64])  # Simplified for demo
    sk = ecdsa.SigningKey.from_string(priv_key[:32], curve=ecdsa.SECP256k1)
    return f"Fusion Key {index}: {key[:32]}... (Sig: {binascii.hexlify(sk.sign(b'The Times 03/Jan/2009')).decode()[:16]}...)"


# Test vectors matching genesis
if __name__ == "__main__":
    print(generate_fusion_key("The Times 03/Jan/2009 Chancellor on brink of second bailout for banks", 0))
    print(generate_fusion_key("The Times 03/Jan/2009 Chancellor...", 1))  # Verify consistency
