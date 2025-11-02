from pathlib import Path

from eth_account import Account

from echo_puzzle_lab.data import load_records

from echo.proof_of_computation import (
    ProofOfComputationService,
    PolygonProofRecorder,
    PuzzleProofVerifier,
    load_proof_ledger,
)


def _solution_fixture(tmp_path: Path, puzzle_id: int) -> Path:
    record = next(entry for entry in load_records() if entry.puzzle == puzzle_id)
    solution = tmp_path / f"puzzle_{puzzle_id}.md"
    solution.write_text(
        "\n".join(
            [
                f"# Puzzle #{puzzle_id:05d} Solution",
                "",
                f"- Provided hash160: `{record.hash160}`",
                "- Bitcoin network version byte: `0x00`",
                f"- Base58Check encoding: `{record.address}`",
                "",
                "```",
                record.address,
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return solution


def test_puzzle_verifier_extracts_proof(tmp_path: Path) -> None:
    verifier = PuzzleProofVerifier()
    solution = _solution_fixture(tmp_path, 10)
    proof = verifier.verify(10, solution_path=solution)
    record = next(entry for entry in load_records() if entry.puzzle == 10)

    assert proof.puzzle_id == 10
    assert proof.hash160 == record.hash160.lower()
    assert proof.base58check == proof.record_address == record.address
    assert proof.digest
    assert len(proof.digest) == 64
    assert "solution_path" in proof.metadata


def test_service_records_stub_ledger(tmp_path: Path) -> None:
    verifier = PuzzleProofVerifier()
    solution = _solution_fixture(tmp_path, 10)
    private_key = Account.create().key.hex()
    ledger_path = tmp_path / "proof_ledger.json"
    recorder = PolygonProofRecorder(private_key, ledger_path=ledger_path, chain_id=80002)
    service = ProofOfComputationService(verifier, recorder)

    submission = service.process_puzzle(10, solution_path=solution)

    assert submission.puzzle_id == 10
    assert submission.signature.startswith("0x")
    assert submission.tx_hash.startswith("0x")
    assert submission.chain_id == 80002
    assert ledger_path.exists()

    ledger = load_proof_ledger(ledger_path)
    assert ledger and ledger[0]["puzzle"] == 10
    assert ledger[0]["hash160"] == submission.hash160
    assert ledger[0]["metadata"]["mode"] == "stub"
