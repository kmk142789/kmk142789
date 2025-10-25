import json
from hashlib import sha256
from pathlib import Path

from cognitive_harmonics.harmonix_evolver import EchoEvolver
from cognitive_harmonics.harmonic_memory_serializer import canonical_checksum
from satoshi.puzzle_dataset import load_puzzle_solutions


def test_cycle_snapshot_persists_and_matches_schema() -> None:
    target = Path("harmonic_memory/cycles/cycle_00001.json")
    if target.exists():
        target.unlink()

    evolver = EchoEvolver()
    state, payload = evolver.run_cycle()

    snapshot_path = evolver.last_cycle_snapshot_path
    assert snapshot_path is not None
    try:
        assert snapshot_path == target
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))

        schema = json.loads(Path("harmonic_memory/schema.json").read_text(encoding="utf-8"))
        expected_top_level = set(schema["parameters"]["properties"].keys())
        assert set(data.keys()) == expected_top_level

        assert isinstance(data["user_music_preference"], str)
        assert f"cycle-{state.cycle:05d}" in data["user_music_preference"]
        complexity_parts = dict(part.split(":", 1) for part in data["lyrical_complexity"].split("|"))
        assert complexity_parts["payload-checksum"] == canonical_checksum(payload)[:12]
        assert data["adaptive_evolution"] is True

        cycle_snapshot = data["cycle_snapshot"]
        cycle_schema = schema["parameters"]["properties"]["cycle_snapshot"]["properties"]
        assert set(cycle_snapshot.keys()) == set(cycle_schema.keys())

        assert cycle_snapshot["cycle_id"] == state.cycle
        puzzle_entry = load_puzzle_solutions()[state.cycle - 1]
        puzzle_block = cycle_snapshot["puzzle"]
        assert puzzle_block["puzzle_id"] == f"puzzle-{puzzle_entry.bits:03d}"
        assert puzzle_block["address"] == puzzle_entry.address
        assert puzzle_block["hash160"] == puzzle_entry.hash160_compressed.lower()
        assert puzzle_block["checksums"]["address_sha256"] == sha256(
            puzzle_entry.address.encode("utf-8")
        ).hexdigest()

        assert cycle_snapshot["state"] == evolver.snapshot_state()
        assert cycle_snapshot["payload"] == payload

        assert cycle_snapshot["checksums"]["state_sha256"] == canonical_checksum(
            cycle_snapshot["state"]
        )
        assert cycle_snapshot["checksums"]["payload_sha256"] == canonical_checksum(
            cycle_snapshot["payload"]
        )

        artifact = cycle_snapshot["artifact"]
        assert artifact["path"] == str(EchoEvolver.artifact_path)
        assert cycle_snapshot["checksums"]["artifact_sha256"] == sha256(
            artifact["body"].encode("utf-8")
        ).hexdigest()
    finally:
        if snapshot_path and snapshot_path.exists():
            snapshot_path.unlink()
