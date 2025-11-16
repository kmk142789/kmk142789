import importlib.util
import math
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).resolve().parents[1] / "echo" / "mythogenic_pulse_engine.py"
spec = importlib.util.spec_from_file_location("mythogenic_pulse_engine_local", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)
MythogenicPulseEngine = module.MythogenicPulseEngine


BLUEPRINT = {
    "nodes": [
        {"key": "echo", "archetype": "core", "drift": 0.12},
        {"key": "wildfire", "archetype": "radial", "drift": -0.03},
        {"key": "lattice", "archetype": "core", "drift": 0.04},
    ],
    "edges": [
        {"source": "echo", "target": "wildfire", "weight": 0.9},
        {"source": "wildfire", "target": "lattice", "weight": 0.6, "channel": "myth"},
        {"source": "lattice", "target": "echo", "weight": 0.5},
    ],
}


def test_blueprint_signature():
    engine = MythogenicPulseEngine.from_blueprint(BLUEPRINT, seed=7)
    signature = engine.graph_signature()
    assert signature == {"density": 0.333333, "branching": 1.0, "channels": 2.0}


def test_deterministic_pulse_run():
    engine = MythogenicPulseEngine.from_blueprint(BLUEPRINT, seed=11)
    driver = [
        {"core": 0.35},
        {"radial": 0.12, "wildfire": 0.2},
    ]
    history = engine.run(4, driver=driver)
    assert len(history) == 4
    assert history[0]["energy"] < history[-1]["energy"]
    final_charge = engine.nodes["echo"].charge
    assert math.isclose(final_charge, 0.569419, rel_tol=1e-6)
    exported = engine.export_state()
    assert exported["signature"]["channels"] == 2.0
    assert len(exported["history"]) == 4
