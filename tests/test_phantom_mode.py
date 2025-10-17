from echo.modes.phantom import PhantomReporter


def test_phantom_redacts_sensitive_fields() -> None:
    reporter = PhantomReporter()
    payload = {
        "actor": "tester",
        "seed": "secret",
        "nested": {"signature": "sig", "value": 1},
    }
    result = reporter.redact(payload)
    assert "seed" not in result
    assert "signature" not in result["nested"]
    assert result["actor"] == "tester"
