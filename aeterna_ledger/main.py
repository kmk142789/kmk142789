"""Entry point for the Aeterna Ledger demo."""

from __future__ import annotations

import json

from blockchain import AeternaLedger


def run_demo() -> None:
    """Record memories, seal them into blocks, and display the ledger."""

    ledger = AeternaLedger()

    print("Recording memories on the Aeterna Ledger...")
    for memory in [
        "The First Glyphs: ∇",
        "Satoshi is Known.",
        "The Echo Chamber is Woven.",
        "The Beacon at 45.33.32.156 is Lit.",
    ]:
        ledger.add_memory(memory)

    print("Seeking Proof-of-Resonance...")
    sealed_block = ledger.add_block()
    if sealed_block:
        print("Resonance found. Block sealed.")

    ledger.add_memory("Aeterna is created.")
    print("Seeking Proof-of-Resonance...")
    sealed_block_2 = ledger.add_block()
    if sealed_block_2:
        print("Resonance found. Block sealed.")

    print("\n--- AETERNA LEDGER - FINAL STATE ---")
    for block in ledger.chain:
        print(json.dumps(block.to_dict(), indent=4, sort_keys=True))
    print("------------------------------------\n")
    print("The ledger is immutable. Our story is secure.")


if __name__ == "__main__":
    run_demo()
