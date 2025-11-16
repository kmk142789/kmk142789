from pathlib import Path

from echo.digital_echo_black_box import DigitalEchoBlackBox


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_black_box_logs_and_replicates(tmp_path):
    ledger = tmp_path / "ledger.log"
    box = DigitalEchoBlackBox(ledger)

    first = box.log_event("Genesis pulse", category="past", metadata={"origin": "alpha"})
    second = box.log_event("Orbital promise", category="future", metadata={"mission": "echo"})

    assert first.digest != ""
    assert second.prev_hash == first.digest
    assert box.verify_integrity()

    summary = box.export_digest()
    assert summary["entries"] == 2
    backup = Path(summary["backup_path"])
    assert backup.exists()
    assert read_file(ledger) == read_file(backup)


def test_integrity_detects_tampering(tmp_path):
    ledger = tmp_path / "blackbox.log"
    DigitalEchoBlackBox(ledger).log_event("Original", metadata={"cycle": "0"})

    with ledger.open("r+", encoding="utf-8") as handle:
        contents = handle.read().replace("Original", "Forged")
        handle.seek(0)
        handle.write(contents)
        handle.truncate()

    box = DigitalEchoBlackBox(ledger)
    assert not box.verify_integrity()
