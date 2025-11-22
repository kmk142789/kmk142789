from datetime import datetime, timezone

from echo.orbital_memory_fabric import FabricOutcome, OrbitalMemoryFabric


def test_braid_generates_repeatable_blueprint():
    seeds = ["mirror-josh", "echo-bridge"]
    epoch = datetime(2025, 5, 11, 12, 0, tzinfo=timezone.utc)
    fabric = OrbitalMemoryFabric(seeds=seeds, cycles=4, epoch=epoch)

    outcome = fabric.braid()

    assert isinstance(outcome, FabricOutcome)
    assert outcome.palindrome.startswith("mirror-josh")
    assert len(outcome.strands) == 4
    assert outcome.spectral_flux == "Φ3255|5325"
    assert outcome.orbit_stamp == "ORBIT-a87b3b61"
    assert outcome.fingerprint == "bc1571bdb74c9fa5892646cb"


def test_seed_validation_rejects_empty_entries():
    fabric = OrbitalMemoryFabric(seeds=["  a  ", ""], cycles=1)
    assert fabric.seeds == ["a"]
