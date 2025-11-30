from echo.evolver import EchoEvolver


def test_propagation_report_reflects_cached_ledger_and_health() -> None:
    evolver = EchoEvolver()
    evolver.advance_cycle()

    events = evolver.propagate_network(enable_network=False)
    report = evolver.propagation_report()

    assert report["cycle"] == evolver.state.cycle
    assert report["events"] == events
    assert report["channels"] == len(events)
    assert report["mode"] == "simulated"
    assert report["health"]["mode"] == "simulated"
    assert report["timeline_length"] >= 1
    assert report["ledger_verified"] is True
    assert report.get("timeline_hash") == evolver.state.network_cache.get(
        "propagation_timeline_hash"
    )

    preview = report["timeline_preview"]
    if preview:
        preview[0]["summary"] = "mutated"
        cached_preview = evolver.state.network_cache["propagation_ledger"]
        assert cached_preview[0]["summary"] != "mutated"


def test_propagation_report_embeds_into_artifact_payload() -> None:
    evolver = EchoEvolver()
    evolver.advance_cycle()
    evolver.propagate_network(enable_network=False)

    prompt = {
        "title": "propagation",
        "mantra": "safeguarded",
        "caution": "non-executable",
    }
    payload = evolver.artifact_payload(prompt=prompt)

    propagation = payload["propagation"]
    assert propagation["cycle"] == evolver.state.cycle
    assert propagation["channels"] == len(propagation["events"])

    # Mutations to the returned payload should not alter cached propagation entries.
    cached_events = list(evolver.state.network_cache["propagation_events"])
    propagation["events"].append("extra")
    assert evolver.state.network_cache["propagation_events"] == cached_events
