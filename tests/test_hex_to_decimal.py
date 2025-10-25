from tools.hex_to_decimal import hex_to_decimal


def test_hex_to_decimal_basic_conversion():
    lines = [
        "00000000000000000000000000000000000000000000000000000000000000e2",
        "0x0f",
        "",
        "000000000000000000000000000000000000000000000000000000000000010e",
    ]

    assert hex_to_decimal(lines) == [226, 15, 270]


def test_hex_to_decimal_rejects_invalid_values():
    lines = ["xyz"]

    try:
        hex_to_decimal(lines)
    except ValueError as exc:
        assert "Line 1 is not valid hexadecimal" in str(exc)
    else:  # pragma: no cover - defensive path
        raise AssertionError("Expected ValueError to be raised")
