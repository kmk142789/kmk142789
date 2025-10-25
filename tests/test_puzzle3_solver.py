"""Regression tests for the hand-rolled Puzzle #3 solver."""

from echo.tools.puzzle3_solver import derive_puzzle3_solution


def test_puzzle3_solution_matches_known_values():
    solution = derive_puzzle3_solution()

    assert solution["private_key_decimal"] == "7"
    assert solution["private_key_hex"] == "07"
    assert (
        solution["public_key_compressed"]
        == "025cbdf0646e5db4eaa398f365f2ea7a0e3d419b7e0330e39ce92bddedcac4f9bc"
    )
    assert solution["hash160"] == "5dedfbf9ea599dd4e3ca6a80b333c472fd0b3f69"
    assert solution["address"] == "19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA"
    assert solution["pkscript"] == (
        "OP_DUP OP_HASH160 5dedfbf9ea599dd4e3ca6a80b333c472fd0b3f69 "
        "OP_EQUALVERIFY OP_CHECKSIG"
    )
