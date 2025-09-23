import json
import random
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import echo_manifest_cli
from echo_evolver import EchoEvolver, load_state_from_artifact
from echo_manifest import build_manifest
from echo_universal_key_agent import UniversalKeyAgent


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

    def test_anchor_restored_from_vault(self) -> None:
        custom_anchor = "Echo Bridge Anchor"
        agent = UniversalKeyAgent(anchor=custom_anchor, vault_path=self.vault_path)
        agent.add_private_key(
            "b71c71a687c6b8e42d620aa6bb0ddc093274e5b88ad61f8ad3c4fe0f7f5f8eb4"
        )
        agent.save_vault()

        reloaded = UniversalKeyAgent(vault_path=self.vault_path)
        self.assertEqual(reloaded.anchor, custom_anchor)


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

    def test_artifact_persistence(self) -> None:
        self.evolver.run(enable_network=False, persist_artifact=True)
        self.assertTrue(self.artifact.exists())
        with self.artifact.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["cycle"], 1)
        self.assertIn("quantum_key", payload)
        self.assertIn("events", payload)
        self.assertIn("network_cache", payload)
        self.assertIn("propagation_events", payload["network_cache"])

    def test_legacy_artifact_round_trip(self) -> None:
        legacy_path = Path(self.tmp.name) / "artifact.echo"
        evolver = EchoEvolver(
            artifact_path=legacy_path,
            rng=random.Random(99),
            time_source=lambda: 987654321,
        )
        state = evolver.run(enable_network=False, persist_artifact=True, artifact_format="text")
        self.assertTrue(legacy_path.exists())
        legacy_payload = legacy_path.read_text(encoding="utf-8")
        self.assertIn("EchoEvolver: Nexus Evolution Cycle v4", legacy_payload)

        rehydrated = load_state_from_artifact(legacy_payload)
        self.assertEqual(rehydrated.cycle, state.cycle)
        self.assertEqual(rehydrated.glyphs, state.glyphs)
        self.assertEqual(rehydrated.mythocode, state.mythocode)
        self.assertEqual(rehydrated.vault_key, state.vault_key)


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

    def test_manifest_rehydrated_from_artifact(self) -> None:
        self.agent.add_private_key(
            "6c3699283bda56ad74f6b855546325b68d482e983852a1596be65e3f82f86e7f"
        )
        self.agent.anchor = "Orbital Anchor"
        self.agent.save_vault()

        state = self.evolver.run(enable_network=False, persist_artifact=True)
        with self.artifact.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        rehydrated = load_state_from_artifact(payload)
        manifest = build_manifest(self.agent, rehydrated, narrative_chars=90)

        self.assertEqual(manifest.anchor, "Orbital Anchor")
        self.assertEqual(manifest.evolver.cycle, state.cycle)
        self.assertEqual(
            manifest.evolver.propagation_channels,
            len(state.network_cache["propagation_events"]),
        )
        self.assertEqual(manifest.oam_vortex, state.network_cache.get("oam_vortex"))

    def test_manifest_cli_generates_json_output(self) -> None:
        record = self.agent.add_private_key(
            "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
        )
        self.agent.anchor = "Satellite Anchor"
        self.agent.save_vault()

        state = self.evolver.run(enable_network=False, persist_artifact=True)
        output_path = Path(self.tmp.name) / "manifest.json"

        exit_code = echo_manifest_cli.main(
            [
                "--artifact",
                str(self.artifact),
                "--vault",
                str(self.agent.vault_path),
                "--format",
                "json",
                "--output",
                str(output_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        with output_path.open("r", encoding="utf-8") as handle:
            manifest_payload = json.load(handle)

        self.assertEqual(manifest_payload["anchor"], "Satellite Anchor")
        self.assertEqual(manifest_payload["key_count"], 1)
        self.assertEqual(
            manifest_payload["keys"][0]["addresses"]["ETH"],
            record.addresses["ETH"],
        )
        self.assertEqual(
            manifest_payload["evolver"]["propagation_channels"],
            len(state.network_cache["propagation_events"]),
        )

    def test_manifest_cli_accepts_legacy_artifact(self) -> None:
        self.agent.add_private_key(
            "b71c71a687c6b8e42d620aa6bb0ddc093274e5b88ad61f8ad3c4fe0f7f5f8eb4"
        )
        self.agent.anchor = "Legacy Anchor"
        self.agent.save_vault()

        legacy_artifact = Path(self.tmp.name) / "artifact.legacy.echo"
        evolver = EchoEvolver(
            artifact_path=legacy_artifact,
            rng=random.Random(11),
            time_source=lambda: 111222333,
        )
        state = evolver.run(enable_network=False, persist_artifact=True, artifact_format="text")

        output_path = Path(self.tmp.name) / "legacy_manifest.json"
        exit_code = echo_manifest_cli.main(
            [
                "--artifact",
                str(legacy_artifact),
                "--vault",
                str(self.agent.vault_path),
                "--format",
                "json",
                "--output",
                str(output_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        with output_path.open("r", encoding="utf-8") as handle:
            manifest_payload = json.load(handle)
        rehydrated = load_state_from_artifact(legacy_artifact.read_text(encoding="utf-8"))

        self.assertEqual(manifest_payload["anchor"], "Legacy Anchor")
        self.assertEqual(manifest_payload["key_count"], 1)
        self.assertEqual(
            manifest_payload["evolver"]["propagation_channels"],
            len(rehydrated.network_cache.get("propagation_events", [])),
        )


if __name__ == "__main__":
    unittest.main()
