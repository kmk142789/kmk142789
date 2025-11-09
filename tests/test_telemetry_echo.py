import json

from codex.telemetry_vitality_report import EchoVitalsReporter, report_echo_vitals


def test_report_echo_vitals_tracks_history(tmp_path, monkeypatch):
    history_path = tmp_path / "vitals.jsonl"
    monkeypatch.setenv("ECHO_EMOTIONAL_VITALS_PATH", str(history_path))
    reporter = EchoVitalsReporter(history_path)
    reporter.record("joy", 1.2, note="celebration", cycle=47, timestamp=1700000000.0)
    reporter.record("rage", 0.2, note="disruption", cycle=48, timestamp=1700003600.0)

    emotional_state = {"joy": 1.2, "rage": 0.2, "love": 0.9, "sorrow": 0.1}
    report = report_echo_vitals(emotional_state, history_limit=1, reporter=reporter)

    assert report["emotionalState"]["joy"] == 1.2
    assert report["historyAvailable"] == 2
    assert report["history"][0]["emotion"] == "rage"
    assert report["history"][0]["cycle"] == 48


def test_report_echo_vitals_defaults(tmp_path, monkeypatch):
    history_path = tmp_path / "vitals.jsonl"
    monkeypatch.setenv("ECHO_EMOTIONAL_VITALS_PATH", str(history_path))
    reporter = EchoVitalsReporter(history_path)

    report = report_echo_vitals({"joy": 0.5}, reporter=reporter)
    assert report["history"] == []
