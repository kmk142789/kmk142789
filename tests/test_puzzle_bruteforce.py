from scripts import puzzle_bruteforce as pb


def test_public_keys_from_private_key_one() -> None:
    compressed, uncompressed = pb.public_keys_from_private(1)
    assert (
        compressed.hex()
        == "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
    )
    assert (
        uncompressed.hex()
        == (
            "0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            "483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8"
        )
    )


def test_p2pkh_addresses_private_key_one() -> None:
    compressed, uncompressed = pb.public_keys_from_private(1)
    assert pb.p2pkh_address(compressed) == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    assert pb.p2pkh_address(uncompressed) == "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm"


def test_private_key_to_wif() -> None:
    assert (
        pb.private_key_to_wif(1, compressed=False)
        == "5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf"
    )
    assert (
        pb.private_key_to_wif(1, compressed=True)
        == "KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn"
    )
