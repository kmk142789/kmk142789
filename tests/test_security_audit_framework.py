from security.audit_framework import AuditTarget, FrameworkConfig, SecurityAuditFramework


def test_framework_detects_secret_and_dependency_issues(tmp_path):
    sensitive = tmp_path / "secrets.env"
    sensitive.write_text("token=abc" * 200)
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("flask>=2.0\nrequests==2.28.2\n")

    framework = SecurityAuditFramework()
    targets = [AuditTarget(name="fixture", path=str(tmp_path))]
    signals = framework.run(targets)

    assert "fixture" in signals
    descriptions = [signal.finding.description for signal in signals["fixture"]]
    assert any("Suspicious artefact" in desc for desc in descriptions)
    assert any("not pinned" in desc for desc in descriptions)


def test_framework_threshold_flags_actionable(tmp_path):
    world_writable = tmp_path / "config.txt"
    world_writable.write_text("data")
    world_writable.chmod(0o777)

    framework = SecurityAuditFramework()
    targets = [AuditTarget(name="fixture", path=str(tmp_path))]
    config = FrameworkConfig(fail_on_score=0.6)
    signals = framework.run(targets, config)

    flagged = [signal for signal in signals["fixture"] if signal.is_actionable(config.fail_on_score)]
    assert flagged
    assert any(signal.category == "configuration" for signal in flagged)
