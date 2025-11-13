from tools.derive_puzzle_address import PuzzleAddressError, hash160_to_p2pkh


def test_puzzle_71_reconstruction():
    result = hash160_to_p2pkh("bf47ed67cc10c9d5c924084b89b65bf17ac8cbff")
    assert result.address == "1JSQEExCz8uz11WCd7ZLpZVqBGMzGGNNF8"


def test_puzzle_72_reconstruction():
    result = hash160_to_p2pkh("0c185494a6d9a37cc3830861743586be21480356")
    assert result.address == "126xFopqfGmJcAqrLpHtBNn3RCXG3cWtmE"


def test_invalid_hash_length():
    try:
        hash160_to_p2pkh("abcd")
    except PuzzleAddressError as exc:
        assert "20-byte" in str(exc)
    else:
        raise AssertionError("expected PuzzleAddressError for invalid length")
