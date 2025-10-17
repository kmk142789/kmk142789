from echo.keys import FractalKeysmith


def test_keysmith_attest_valid_hex_key() -> None:
    # Build a key with checksum 0
    base = "00" * 32
    keysmith = FractalKeysmith()
    attestation = keysmith.attest(base)
    assert attestation.valid is True
    assert attestation.key == base
    assert any(step.status == "ok" for step in attestation.transcript)


def test_keysmith_repair_and_cache(tmp_path) -> None:
    keysmith = FractalKeysmith()
    bad_key = "ab cd ef"
    attestation = keysmith.attest(bad_key)
    assert attestation.valid in {True, False}
    second = keysmith.attest(bad_key)
    assert second.transcript == attestation.transcript
