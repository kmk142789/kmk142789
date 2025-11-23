from pathlib import Path

from scripts.crown_registry import CrownRegistry, Registry, TldRecord


def test_mint_and_revision(tmp_path: Path) -> None:
    db = tmp_path / "registry.json"
    zone = tmp_path / "zone.txt"
    registry = CrownRegistry(db_path=db, zone_path=zone)

    first = registry.mint_tld("echo", "owner", "purpose")
    assert first.revision == 1
    assert first.auth_key

    second = registry.mint_tld("ECHO", "owner", "purpose")
    assert second.revision == 2
    assert registry.registry.tlds["echo"].revision == 2


def test_sign_root_zone_outputs_records(tmp_path: Path) -> None:
    db = tmp_path / "registry.json"
    zone = tmp_path / "zone.txt"
    registry = CrownRegistry(db_path=db, zone_path=zone)
    registry.mint_tld("love", "anchor", "storage")

    content = registry.sign_root_zone()
    saved = Registry.from_file(db)

    assert "; AUTHORITY: Our Forever Love" in content
    assert "LOVE" in content.upper()
    assert "AUTH_KEY" in content
    assert "love" in saved.tlds
    assert zone.read_text(encoding="utf-8") == content


def test_bootstrap_defaults(tmp_path: Path) -> None:
    registry = CrownRegistry(db_path=tmp_path / "registry.json", zone_path=tmp_path / "zone.txt")
    registry.bootstrap_defaults()

    tlds = {record.tld for record in registry.list_tlds()}
    assert {"echo", "josh", "nexus", "sovereign", "love", "null"}.issubset(tlds)
