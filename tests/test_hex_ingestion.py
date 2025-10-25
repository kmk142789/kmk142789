from __future__ import annotations

from pathlib import Path

from echo.hex_ingestion import IngestionDaemonHex


def _write_payload(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_ingestion_daemon_reports_meaningful_ascii(tmp_path: Path) -> None:
    payload = _write_payload(tmp_path / "greeting.hex", "48656c6c6f20576f726c64")

    daemon = IngestionDaemonHex(tmp_path)
    reports = daemon.scan_once()

    assert [report.path for report in reports] == [payload]
    report = reports[0]

    assert report.ascii_text == "Hello World"
    assert report.decimals and report.decimals[0] > 0
    assert any(alert.code == "meaningful-ascii" for alert in report.anomalies)

    map_text = report.resonance_map.render()
    assert "Hex Resonance Map" in map_text
    assert "Hello World" in map_text

    # Subsequent scans should not duplicate the processed payload when unchanged.
    assert daemon.scan_once() == []


def test_ingestion_daemon_flags_decode_errors(tmp_path: Path) -> None:
    payload = _write_payload(tmp_path / "broken.hex", "this-is-not-hex")

    daemon = IngestionDaemonHex(tmp_path)
    reports = daemon.scan_once()

    assert [report.path for report in reports] == [payload]
    report = reports[0]

    codes = {alert.code for alert in report.anomalies}
    assert "ascii-decode-error" in codes
    assert "decimal-decode-error" in codes
    assert report.ascii_text is None
    assert not report.decimals
    assert report.resonance_map.glyph_band == "∇⊸≋∇"
