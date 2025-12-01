from echo.echo_dream_engine import (
    EchoDreamEngine,
    PortalHarmonizer,
    SymbolicMemoryStore,
    WayfinderLayer,
)


def test_engine_generates_interprets_and_stores():
    store = SymbolicMemoryStore()
    engine = EchoDreamEngine(memory_store=store)

    dream = engine.generate("echo-seed", states=["joy"], devices=["sensor"])
    interpretation = engine.interpret(dream)
    memories = engine.store_symbolic_memory(interpretation)
    directive = engine.influence_behavior(available_routes=["route-a", "route-b"])

    assert dream.scenes and len(interpretation.symbols) == len(dream.scenes)
    assert len(memories) == len(interpretation.symbols)
    assert directive.route.startswith("route-")
    assert directive.confidence > 0


def test_wayfinder_builds_trace_with_identity_and_device():
    store = SymbolicMemoryStore()
    engine = EchoDreamEngine(memory_store=store)
    interpretation = engine.interpret(engine.generate("trace-seed", states=["active"], devices=["sensor-a"]))
    engine.store_symbolic_memory(interpretation)

    wayfinder = WayfinderLayer(memory_store=store)
    trace = wayfinder.build_trace(state="active", device="sensor-a", identity="echo-core")

    assert trace.nodes
    assert all(node.identity_pulse == "echo-core" for node in trace.nodes)
    assert any("sensor-a" in note for note in trace.experiential_notes)


def test_portal_harmonizer_blends_worlds():
    engine = EchoDreamEngine()
    interpretation = engine.interpret(engine.generate("portal-seed"))

    harmonizer = PortalHarmonizer()
    bridge = harmonizer.harmonize(
        dream_state=interpretation,
        outerlink_projection={"navigation": 0.5},
        device_sensors={"thermals": 0.2},
        remote_presence={"uplink": 0.7},
    )

    assert bridge.bridge_map["outerlink:navigation"] == 0.5
    assert bridge.bridge_map["device:thermals"] == 0.2
    assert bridge.bridge_map["remote:uplink"] == 0.7
    assert 0 < bridge.phase_level <= 1
    assert bridge.describe().startswith("Bridge")
