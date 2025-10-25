from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from satoshi import puzzle_script_cli


EXPECTED_SCRIPT_LINES = [
    "OP_DUP",
    "OP_HASH160",
    "97f9281a1383879d72ac52a6a3e9e8b9a4a4f655",
    "OP_EQUALVERIFY",
    "OP_CHECKSIG",
]


@pytest.mark.parametrize("bits", [14])
def test_cli_outputs_canonical_script(bits: int) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = puzzle_script_cli.main([str(bits)])

    assert exit_code == 0
    assert buffer.getvalue().strip().splitlines() == EXPECTED_SCRIPT_LINES


def test_cli_supports_single_line_output() -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = puzzle_script_cli.main(["14", "--single-line"])

    assert exit_code == 0
    assert buffer.getvalue().strip() == " ".join(EXPECTED_SCRIPT_LINES)


@pytest.mark.parametrize("bits", [0, -1])
def test_cli_rejects_non_positive_bit_lengths(bits: int) -> None:
    with pytest.raises(SystemExit) as exc_info:
        puzzle_script_cli.main([str(bits)])

    assert exc_info.value.code == 2


def test_cli_surfaces_missing_entries() -> None:
    with pytest.raises(SystemExit) as exc_info:
        puzzle_script_cli.main(["9999"])

    assert exc_info.value.code == 1
