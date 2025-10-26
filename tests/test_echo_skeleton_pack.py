from __future__ import annotations

import json
from pathlib import Path

import pytest

import skeleton_key_core as skeleton


TEST_SECRET = "Echo skeleton integration test"
EXPECTED_PRIV = "a8f73412c98967365c0b29d54676db86d27a34501f55a24b4b18ce2bf60eaa38"
EXPECTED_WIF = "L2tA7mt9RtQRP9ok3UFqXhvmFx3So3cprFU9udaWvVoiAoj5URfP"
EXPECTED_ETH = "0x2e22f4b1ac0028bf9cc5710449e6ed888d30ec68"


@pytest.fixture(scope="module")
def derived_key() -> skeleton.DerivedKey:
    secret = skeleton.read_secret_from_phrase(TEST_SECRET)
    return skeleton.derive_from_skeleton(secret, "core", 0)


def test_derive_from_phrase_matches_expected(derived_key: skeleton.DerivedKey) -> None:
    assert derived_key.priv_hex == EXPECTED_PRIV
    assert derived_key.btc_wif == EXPECTED_WIF
    assert derived_key.eth_address == EXPECTED_ETH


def test_read_secret_from_file(tmp_path: Path) -> None:
    secret_path = tmp_path / "secret.skel"
    secret_path.write_text(TEST_SECRET + "\n", encoding="utf-8")
    secret = skeleton.read_secret_from_file(secret_path)
    assert secret == TEST_SECRET.encode()


def test_sign_claim_is_deterministic(derived_key: skeleton.DerivedKey) -> None:
    message = "EchoClaim/v1\nasset=test\nnamespace=core\nindex=0"
    signature = skeleton.sign_claim(derived_key.priv_hex, message)
    second = skeleton.sign_claim(derived_key.priv_hex, message)
    assert signature["algo"] == second["algo"]
    assert signature["sig"] == second["sig"]
    if signature["algo"] == "ecdsa-secp256k1":
        assert signature["pub"] == second["pub"]
    else:
        assert signature["pub"] is None


def test_derive_cli_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStdout:
        def __init__(self) -> None:
            self.buffer: list[str] = []

        def write(self, text: str) -> None:
            self.buffer.append(text)

        def getvalue(self) -> str:
            return "".join(self.buffer)

    dummy = DummyStdout()
    monkeypatch.setattr("sys.stdout", dummy)
    argv = ["--phrase", TEST_SECRET, "--json"]
    assert skeleton.derive_cli(argv) == 0
    payload = json.loads(dummy.getvalue())
    assert payload["eth_priv_hex"] == EXPECTED_PRIV
    assert payload["btc_wif"] == EXPECTED_WIF


def test_claim_cli_emits_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_path = tmp_path / "claim.json"

    class DummyStdout:
        def __init__(self) -> None:
            self.buffer: list[str] = []

        def write(self, text: str) -> None:
            self.buffer.append(text)

        def getvalue(self) -> str:
            return "".join(self.buffer)

    dummy = DummyStdout()
    monkeypatch.setattr("sys.stdout", dummy)

    argv = [
        "--phrase",
        TEST_SECRET,
        "--asset",
        "github-repo:EXAMPLE/DEMO",
        "--out",
        str(output_path),
        "--stdout",
    ]
    assert skeleton.claim_cli(argv) == 0
    on_disk = json.loads(output_path.read_text(encoding="utf-8"))
    text = dummy.getvalue()
    json_blob = text[text.find("{") :]
    echoed = json.loads(json_blob)
    assert on_disk["asset"] == "github-repo:EXAMPLE/DEMO"
    assert on_disk["signature"]["sig"] == echoed["signature"]["sig"]
