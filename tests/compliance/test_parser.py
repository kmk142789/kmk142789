from pathlib import Path

from compliance.parser.markdown_parser import parse_markdown


def test_parse_charter_clause_metadata():
    artifact = parse_markdown(Path("identity/aster_charter.md"))
    clause = next(cl for cl in artifact.clauses() if cl.id == "CH-AUTH-001")
    assert clause.tags == ["authority", "quorum", "flow"]
    assert clause.structured_data[0].payload["threshold"] == "2-of-3"
    assert clause.source.line_start < clause.source.line_end


def test_parse_trust_emergency_clause():
    artifact = parse_markdown(Path("identity/vault_trust_deed.md"))
    clause = next(cl for cl in artifact.clauses() if cl.id == "TR-CUST-002")
    assert clause.structured_data[0].payload["threshold"] == "1-of-1"
    assert clause.structured_data[0].payload["duration_hours"] == 24
