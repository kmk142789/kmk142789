from __future__ import annotations

from echo.workflows import DigitalIdentityToolkit


def test_digital_identity_toolkit_serialises_program() -> None:
    toolkit = DigitalIdentityToolkit(
        program_name="Lil Footsteps",
        primary_languages=("English", "Spanish"),
        support_email="help@lilfootsteps.org",
        escalation_contact="ops@echo.systems",
        guardianship_review_cadence_weeks=8,
    )

    payload = toolkit.to_dict()

    assert payload["program_name"] == "Lil Footsteps"
    assert len(payload["wallet_options"]) == 3
    assert payload["wallet_options"][0]["name"] == "Magic Link Wallet"

    qr_policy = payload["provider_qr_policy"]
    assert qr_policy["scanner_role"] == "Provider front desk or classroom lead"
    assert "timestamp" in " ".join(qr_policy["verification_steps"])

    support_matrix = payload["support_matrix"]
    assert set(support_matrix.keys()) == {"English", "Spanish"}
    for entries in support_matrix.values():
        assert "Signal" in " ".join(entries)
