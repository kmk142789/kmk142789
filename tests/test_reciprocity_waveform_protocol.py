from datetime import datetime, timedelta, timezone

from src.reciprocity_waveform_protocol import (
    BeneficiarySignal,
    Contribution,
    ReciprocityWaveformProtocol,
)


def test_waveform_produces_pledges_and_manifest():
    reference = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    contributions = [
        Contribution(
            contributor="alice",
            magnitude=10.0,
            intent=0.9,
            timestamp=reference - timedelta(hours=10),
            tags=("water", "solar"),
        ),
        Contribution(
            contributor="bob",
            magnitude=5.0,
            intent=0.7,
            timestamp=reference - timedelta(hours=80),
            tags=("solar",),
        ),
    ]
    beneficiaries = [
        BeneficiarySignal(
            identifier="village-grid",
            need_level=0.9,
            readiness=0.8,
            horizon_hours=48,
            tags=("solar",),
        ),
        BeneficiarySignal(
            identifier="waterkeeper",
            need_level=0.6,
            readiness=0.6,
            horizon_hours=24,
            tags=("water",),
        ),
    ]

    protocol = ReciprocityWaveformProtocol(gratitude_bias=0.6)
    waveform = protocol.synthesize_waveform(contributions, beneficiaries)

    assert waveform.aggregate_energy > 0
    assert 0 < waveform.fairness_index <= 1
    assert waveform.pledge_schedule, "Pledges should be generated for aligned beneficiaries"
    assert waveform.pledge_schedule[0].beneficiary == "village-grid"

    manifest = protocol.manifest(contributions, beneficiaries)
    assert manifest.energy == waveform.aggregate_energy
    assert manifest.fairness == waveform.fairness_index
    assert all("beneficiary" in pledge for pledge in manifest.pledges)
    assert manifest.divergences

