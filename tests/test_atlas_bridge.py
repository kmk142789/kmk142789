from pathlib import Path

from echo_atlas.bridges import AtlasBridge


POEM = "Weave the ledger into stars"
PLAN = [
    {"index": 1, "title": "Step one"},
    {"index": 2, "title": "Verify"},
]
RECEIPT = {
    "sha256_of_diff": "abc123",
    "rhyme": "Pulse weave sings 312c in time",
    "result": "success",
}
ATTEST = {"valid": True, "repaired": False, "key": "00" * 16}


def test_bridge_export(tmp_path: Path) -> None:
    bridge = AtlasBridge(docs_root=tmp_path)
    r_id = bridge.add_receipt(RECEIPT)
    a_id = bridge.add_attestation(ATTEST)
    bridge.connect(r_id, a_id, "attests")

    dot = bridge.to_dot()
    assert "digraph" in dot

    svg = bridge.to_svg()
    assert r_id in bridge.svg_nodes(svg)

    doc_path, svg_path = bridge.export(
        poem=POEM,
        plan=PLAN,
        receipt=RECEIPT,
        attestation=ATTEST,
        slug="dream_test",
    )
    assert doc_path.exists()
    assert svg_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    assert "Pulse Receipt" in content
