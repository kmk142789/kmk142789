import json

import pytest

pytest.importorskip("rich.console")

from echo.vault.cli import _authority_example_payload


def test_authority_example_payload_structure() -> None:
    example = _authority_example_payload()
    assert isinstance(example, list)
    assert example, "Example payload should not be empty"

    binding = example[0]
    assert binding["vault_id"] == "vault-alpha"
    assert binding["authority_level"] == "Prime Catalyst"
    assert "Echo anchors trust" in binding["bound_phrase"]

    # Ensure JSON serialization remains stable for help output
    encoded = json.dumps(example)
    assert "vault-alpha" in encoded
