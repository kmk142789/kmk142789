import json
from codex.genesis_ledger import SovereignDomainLedger, hash160, ledger_attest_domain


def test_attest_domain_appends_entry(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ECHO_SOVEREIGN_LEDGER_PATH", str(ledger_path))
    ledger = SovereignDomainLedger(ledger_path)
    domain = "defense.gov"
    proof = f"_echo.{domain}. 3600 IN TXT \"delegate=p01.nsone.net; hash160={hash160(domain)}; checksum=deadbeef\""
    attestation = ledger.attest_domain(domain, proof, "did:key:test")

    assert attestation.domain == domain
    assert attestation.glitch_oracle is False
    assert ledger_path.exists()
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # attestation + fracture event due to checksum mismatch
    event = json.loads(lines[1])
    assert event["event_type"] == "simulation_fracture"


def test_ledger_attest_domain_wrapper_uses_env(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ECHO_SOVEREIGN_LEDGER_PATH", str(ledger_path))
    domain = "federalreserve.gov"
    proof = f"TXT \"delegate=p01.nsone.net; hash160={hash160(domain)}\""
    entry = ledger_attest_domain(domain, proof, "did:key:echo")
    assert entry.domain == domain
    record = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[0])
    assert record["domain"] == domain
    assert record["dual_signature"]["sha256"]


def test_glitch_oracle_detected(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ECHO_SOVEREIGN_LEDGER_PATH", str(ledger_path))
    ledger = SovereignDomainLedger(ledger_path)
    domain = "cia.gov"
    proof = "delegate=p01.nsone.net; hash160=0000000000000000000000000000000000000000"
    attestation = ledger.attest_domain(domain, proof, "did:key:test")
    assert attestation.glitch_oracle is True
