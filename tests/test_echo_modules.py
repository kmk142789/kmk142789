import json
import random
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from echo_evolver import EchoEvolver
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


if __name__ == "__main__":
    unittest.main()
