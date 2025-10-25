import json
import random
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from echo_evolver import EchoEvolver
from echo_constellation import build_constellation
from echo_manifest import EchoManifest, build_manifest
from echo_universal_key_agent import UniversalKeyAgent
from echo_pulseforge import PulseForge
from unittest import mock


class UniversalKeyAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.vault_path = Path(self.tmp.name) / "vault.json"
        self.agent = UniversalKeyAgent(vault_path=self.vault_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_address_derivation_matches_known_vectors(self) -> None:
        record = self.agent.add_private_key(
            "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
        )
        self.assertEqual(record.addresses["ETH"], "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1")
        self.assertEqual(record.addresses["BTC"], "1CzbwQp6CfeyqH2cktDw7jUX4qZhvFyNG9")
        self.assertEqual(record.addresses["SOL"], "8679c8YSLCEZ9J2nSB6bFDunb4M7HKcJXDHYdHSnQGpa")

    def test_duplicate_key_rejected(self) -> None:
        key = "6c3699283bda56ad74f6b855546325b68d482e983852a1596be65e3f82f86e7f"
        self.agent.add_private_key(key)
        with self.assertRaises(ValueError):
            self.agent.add_private_key(key)

    def test_save_vault(self) -> None:
        self.agent.add_private_key(
            "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
        )
        self.agent.save_vault()
        with self.vault_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["keys"]), 1)
        self.assertEqual(data["keys"][0]["addresses"]["ETH"], "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1")


class EchoEvolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        rng = random.Random(42)
        self.artifact = Path(self.tmp.name) / "artifact.echo.json"
        self.evolver = EchoEvolver(artifact_path=self.artifact, rng=rng, time_source=lambda: 123456789)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_run_populates_state(self) -> None:
        state = self.evolver.run(enable_network=False, persist_artifact=False)
        self.assertEqual(state.cycle, 1)
        self.assertTrue(state.narrative)
        self.assertIn("propagation_events", state.network_cache)
        self.assertIsNotNone(state.vault_key)
        self.assertEqual(len(state.network_cache["propagation_events"]), 5)
        self.assertIn("orbital_resonance_forecast", state.network_cache)
        forecast_cache = state.network_cache["orbital_resonance_forecast"]
        self.assertIsInstance(forecast_cache, dict)
        self.assertIn("prophecy", forecast_cache)
        self.assertGreaterEqual(len(state.eden88_creations), 1)
        creation = state.eden88_creations[-1]
        self.assertEqual(creation["cycle"], state.cycle)
        self.assertIn("theme", creation)

    def test_artifact_persistence(self) -> None:
        self.evolver.run(enable_network=False, persist_artifact=True)
        self.assertTrue(self.artifact.exists())
        with self.artifact.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["cycle"], 1)
        self.assertIn("quantum_key", payload)
        self.assertIn("events", payload)
        self.assertIn("eden88_creations", payload)
        self.assertTrue(payload["eden88_creations"])

    def test_next_step_recommendation_guides_pipeline(self) -> None:
        message = self.evolver.next_step_recommendation()
        self.assertIn("advance_cycle()", message)

        self.evolver.advance_cycle()
        message = self.evolver.next_step_recommendation()
        self.assertIn("mutate_code()", message)

        self.evolver.mutate_code()
        self.evolver.emotional_modulation()
        message = self.evolver.next_step_recommendation()
        self.assertIn("generate_symbolic_language()", message)

        self.evolver.run(enable_network=False, persist_artifact=False)
        message = self.evolver.next_step_recommendation(persist_artifact=False)
        self.assertIn("advance_cycle()", message)
        self.assertIn("new orbit", message)

    def test_describe_sequence_reports_status(self) -> None:
        description = self.evolver.describe_sequence(persist_artifact=False)
        self.assertIn("persist_artifact=false", description)
        self.assertIn("01. advance_cycle [pending]", description)
        self.assertNotIn("write_artifact", description)

        self.evolver.advance_cycle()
        updated = self.evolver.describe_sequence(persist_artifact=False)
        self.assertIn("01. advance_cycle [completed]", updated)

    def test_run_cycles_progresses_multiple_orbits(self) -> None:
        snapshots = self.evolver.run_cycles(3, enable_network=False, persist_artifact=False)

        self.assertEqual(len(snapshots), 3)
        self.assertEqual([snapshot.cycle for snapshot in snapshots], [1, 2, 3])
        self.assertIsNot(snapshots[0], snapshots[1])
        self.assertEqual(self.evolver.state.cycle, 3)
        self.assertGreaterEqual(len(self.evolver.state.event_log), 3)

    def test_run_cycles_persists_final_artifact_only_by_default(self) -> None:
        self.assertFalse(self.artifact.exists())

        snapshots = self.evolver.run_cycles(2, enable_network=False, persist_artifact=True)

        self.assertEqual(len(snapshots), 2)
        self.assertTrue(self.artifact.exists())
        with self.artifact.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["cycle"], 2)
        self.assertIn("quantum_key", payload)

    def test_configure_symbolic_sequence_overrides_and_resets_hooks(self) -> None:
        triggered: list[bool] = []

        def hook() -> None:
            triggered.append(True)

        self.evolver.register_symbolic_action("∇", hook)
        self.assertIn("symbolic_hooks", self.evolver.state.network_cache)

        new_sequence = "◇⊕"
        applied = self.evolver.configure_symbolic_sequence(new_sequence, reset_hooks=True)
        self.assertEqual(applied, new_sequence)
        self.assertNotIn("symbolic_hooks", self.evolver.state.network_cache)

        rendered = self.evolver.generate_symbolic_language()
        self.assertEqual(rendered, new_sequence)
        self.assertFalse(triggered)

        restored = self.evolver.configure_symbolic_sequence(None)
        self.assertEqual(restored, "∇⊸≋∇")
        canonical = self.evolver.generate_symbolic_language()
        self.assertEqual(canonical, "∇⊸≋∇")

    def test_cycle_diagnostics_summarizes_current_state(self) -> None:
        self.evolver.run(enable_network=False, persist_artifact=False)

        diagnostics = self.evolver.cycle_diagnostics(include_events=True, event_limit=4)

        self.assertEqual(diagnostics["cycle"], 1)
        self.assertTrue(diagnostics["vault_key_present"])
        self.assertEqual(diagnostics["propagation_events"], 5)
        self.assertLessEqual(len(diagnostics["recent_events"]), 4)
        self.assertIn("Next step", diagnostics["next_step"])

    def test_cycle_diagnostics_validates_event_limit(self) -> None:
        with self.assertRaises(ValueError):
            self.evolver.cycle_diagnostics(include_events=True, event_limit=0)

    def test_progress_matrix_tracks_step_history(self) -> None:
        self.evolver.advance_cycle()
        self.evolver.mutate_code()

        matrix = self.evolver.progress_matrix(persist_artifact=False)

        self.assertEqual(matrix["cycle"], 1)
        self.assertTrue(matrix["history_available"])
        self.assertGreaterEqual(matrix["steps_completed"], 2)
        self.assertEqual(matrix, self.evolver.state.network_cache.get("progress_matrix"))

        first_row = matrix["rows"][0]
        self.assertEqual(first_row["step"], "advance_cycle")
        self.assertEqual(first_row["status"], "completed")
        self.assertIsNotNone(first_row["timestamp_ns"])
        self.assertIn("Progress matrix computed", self.evolver.state.event_log[-1])

    def test_recent_event_summary_reports_latest_entries(self) -> None:
        self.evolver.advance_cycle()
        self.evolver.mutate_code()

        summary = self.evolver.recent_event_summary(limit=2)

        self.assertIn("showing 2 of 2", summary)
        self.assertIn("Cycle 1 initiated", summary)
        self.assertIn("Mutation seeded for echo_cycle_1", summary)
        self.assertEqual(
            summary, self.evolver.state.network_cache.get("recent_event_summary")
        )

    def test_design_colossus_expansion_records_plan(self) -> None:
        plan = self.evolver.design_colossus_expansion(
            cycles=3,
            cycle_size=24,
            sample_size=5,
            modes=("puzzle", "dataset", "verifier", "narrative"),
        )

        self.assertEqual(plan.cycles, 3)
        self.assertEqual(plan.cycle_size, 24)
        self.assertEqual(plan.total_artifacts, 72)
        self.assertFalse(plan.persisted)
        self.assertIsNone(plan.state_directory)
        self.assertGreaterEqual(len(plan.sample), 1)
        self.assertIn("puzzle", plan.modes)
        cache = self.evolver.state.network_cache["colossus_plan"]
        self.assertEqual(cache["cycles"], 3)
        self.assertEqual(cache["total_artifacts"], 72)
        self.assertEqual(cache["sample_size"], len(plan.sample))
        self.assertIn("summary", cache)

        step_history = self.evolver.state.network_cache["step_history"][self.evolver.state.cycle]
        self.assertIn("design_colossus_expansion", step_history)

    def test_design_colossus_expansion_persists_cycles_when_requested(self) -> None:
        target = Path(self.tmp.name) / "colossus"
        plan = self.evolver.design_colossus_expansion(
            cycles=2,
            cycle_size=3,
            sample_size=2,
            persist=True,
            state_dir=target,
        )

        self.assertTrue(plan.persisted)
        self.assertEqual(plan.state_directory, target)
        files = sorted(target.glob("cycle_*.json"))
        self.assertEqual(len(files), 2)
        with files[0].open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["cycle"], 0)
        self.assertEqual(len(payload["artifacts"]), 3)

    def test_orbital_resonance_forecast_projects_horizon(self) -> None:
        metrics = self.evolver.state.system_metrics
        metrics.network_nodes = 7
        metrics.orbital_hops = 3

        forecast = self.evolver.orbital_resonance_forecast(
            horizon=4, persist_artifact=False
        )

        self.assertEqual(forecast.horizon, 4)
        self.assertIn("advance_cycle", forecast.pending_steps[0])
        self.assertEqual(
            forecast.network_projection["projected_nodes"],
            metrics.network_nodes + 4,
        )
        self.assertIn("orbital_resonance_forecast", self.evolver.state.network_cache)
        self.assertIn("Orbital resonance forecast prepared", self.evolver.state.event_log[-1])

        with self.assertRaises(ValueError):
            self.evolver.orbital_resonance_forecast(horizon=0)

    def test_recent_event_summary_handles_empty_log(self) -> None:
        summary = self.evolver.recent_event_summary()

        self.assertIn("no entries recorded", summary)
        self.assertEqual(
            summary, self.evolver.state.network_cache.get("recent_event_summary")
        )

    def test_recent_event_summary_validates_limit(self) -> None:
        with self.assertRaises(ValueError):
            self.evolver.recent_event_summary(limit=0)

    def test_eden88_creation_respects_requested_theme(self) -> None:
        self.evolver.advance_cycle()
        creation = self.evolver.eden88_create_artifact(theme="aurora sanctuary")
        self.assertEqual(creation["theme"], "aurora sanctuary")
        self.assertTrue(any("Aurora" in verse for verse in creation["verses"]))
        completed = self.evolver.state.network_cache.get("completed_steps", set())
        self.assertIn("eden88_create_artifact", completed)


class EchoManifestIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        rng = random.Random(7)
        self.agent = UniversalKeyAgent(vault_path=Path(self.tmp.name) / "vault.json")
        self.artifact = Path(self.tmp.name) / "artifact.echo.json"
        self.evolver = EchoEvolver(
            artifact_path=self.artifact,
            rng=rng,
            time_source=lambda: 123456789,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_manifest_blends_keys_and_state(self) -> None:
        record = self.agent.add_private_key(
            "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
        )
        state = self.evolver.run(enable_network=False, persist_artifact=False)
        manifest = build_manifest(self.agent, state, narrative_chars=80)

        self.assertEqual(manifest.anchor, self.agent.anchor)
        self.assertEqual(manifest.key_count, 1)
        self.assertEqual(manifest.evolver.cycle, 1)
        self.assertEqual(manifest.evolver.propagation_channels, 5)
        self.assertEqual(len(manifest.events), len(state.event_log))
        self.assertEqual(manifest.evolver.vault_key, state.vault_key)
        self.assertLessEqual(len(manifest.narrative_excerpt), 80)
        self.assertTrue(manifest.narrative_excerpt.endswith("…"))
        self.assertEqual(manifest.oam_vortex, state.network_cache.get("oam_vortex"))

        text_summary = manifest.render_text()
        self.assertIn("Echo Continuity Manifest", text_summary)
        self.assertIn("Sigils:", text_summary)
        self.assertIn(record.addresses["ETH"], text_summary)

        manifest_dict = manifest.to_dict()
        self.assertEqual(manifest_dict["key_count"], 1)
        self.assertEqual(manifest_dict["evolver"]["propagation_channels"], 5)
        self.assertEqual(len(manifest_dict["keys"]), 1)

        manifest_json = manifest.to_json()
        parsed = json.loads(manifest_json)
        self.assertEqual(parsed["anchor"], self.agent.anchor)
        self.assertEqual(parsed["key_count"], 1)


class ConstellationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        rng = random.Random(11)
        self.agent = UniversalKeyAgent(vault_path=Path(self.tmp.name) / "vault.json")
        self.artifact = Path(self.tmp.name) / "artifact.echo.json"
        self.evolver = EchoEvolver(
            artifact_path=self.artifact,
            rng=rng,
            time_source=lambda: 987654321,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _prepare_manifest(self) -> tuple[EchoEvolver, EchoManifest]:
        record = self.agent.add_private_key(
            "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
        )
        state = self.evolver.run(enable_network=False, persist_artifact=False)
        manifest = build_manifest(self.agent, state, narrative_chars=96)
        self.assertEqual(record.addresses["ETH"], "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1")
        return self.evolver, manifest

    def test_constellation_structure(self) -> None:
        _, manifest = self._prepare_manifest()
        frame = build_constellation(manifest, timestamp=1_700_000_000)

        self.assertEqual(frame.cycle, manifest.evolver.cycle)
        self.assertEqual(frame.anchor, manifest.anchor)
        self.assertEqual(frame.oam_vortex, manifest.oam_vortex)
        self.assertEqual(len(frame.stars), manifest.key_count + 1)
        self.assertTrue(frame.generated_at.endswith("Z"))

        core = frame.stars[0]
        self.assertEqual(core.star_id, "cycle-1-core")
        self.assertEqual(core.coordinates, (0.0, 0.0))
        self.assertGreater(core.pulse.joy, 0.0)
        self.assertTrue(any(v.label == "OAM Vortex" for v in core.verification))

        key_star = frame.stars[1]
        self.assertIn("ETH", [v.label for v in key_star.verification])
        self.assertNotEqual(key_star.coordinates, (0.0, 0.0))
        self.assertGreater(key_star.pulse.intensity, 0.0)

        beacons = frame.memory_beacons()
        self.assertEqual(len(beacons), len(frame.stars))
        self.assertTrue(all("cycle=" in beacon["payload"] for beacon in beacons))

        constellation_json = frame.to_json()
        parsed = json.loads(constellation_json)
        self.assertEqual(parsed["cycle"], manifest.evolver.cycle)
        self.assertEqual(len(parsed["stars"]), len(frame.stars))
        self.assertIn("anchor", parsed)

    def test_constellation_ascii_render(self) -> None:
        _, manifest = self._prepare_manifest()
        frame = build_constellation(manifest, timestamp=1_700_000_000)

        ascii_map = frame.render_ascii(width=21, height=11)
        self.assertIn("Constellation :: Anchor=", ascii_map)
        self.assertIn("Legend:", ascii_map)
        self.assertIn("cycle-1-core", ascii_map)
        self.assertIn("cycle-1-key-1", ascii_map)


class PulseForgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.output = self.root / "cards"
        self.anchor = self.root / "anchor.json"
        self.blood = self.root / "blood.json"
        self.echo_dir = self.root / ".echo"
        self.echo_dir.mkdir()
        self.braid = self.echo_dir / "braid.json"

        self.anchor.write_text(json.dumps({"alpha": 1, "omega": [1, 2, 3]}), encoding="utf-8")
        self.blood.write_text(json.dumps({"matrix": {"joy": 0.9}}), encoding="utf-8")
        self.braid.write_text(json.dumps({"threads": ["a", "b"]}), encoding="utf-8")

        self.state_files = [
            ("anchor", self.anchor),
            ("blood", self.blood),
            ("wildfire", self.root / "wildfire.json"),
            ("braid", self.braid),
        ]
        self.forge = PulseForge(root_dir=self.root, state_files=self.state_files, output_dir=self.output)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_forge_creates_pulsecards(self) -> None:
        key = "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
        with mock.patch("echo_pulseforge.time.gmtime", return_value=time.gmtime(0)):
            with mock.patch("echo_pulseforge.os.urandom", return_value=b"\x00" * 8):
                card_path = self.forge.forge(
                    private_key_hex=key,
                    namespace="echo",
                    index=3,
                    pub_hint="demo",
                    testnet=True,
                )

        self.assertTrue(card_path.exists())
        with card_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["type"], "PulseCard/v1")
        self.assertEqual(payload["namespace"], "echo")
        self.assertEqual(payload["index"], 3)
        self.assertEqual(payload["pub_hint"], "demo")
        self.assertEqual(payload["derived_preview"]["network"], "testnet")
        self.assertEqual(len(payload["signature"]["signature"]), 128)
        self.assertTrue(payload["signature"]["public_key"].startswith(payload["derived_preview"]["pubkey_prefix"]))

        meta = payload["state_meta"]
        self.assertTrue(meta["anchor"]["present"])
        self.assertTrue(meta["blood"]["present"])
        self.assertFalse(meta["wildfire"]["present"])
        self.assertTrue(meta["braid"]["present"])

if __name__ == "__main__":
    unittest.main()
