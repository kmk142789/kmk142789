"""Utilities for extracting and indexing Echo puzzle metadata."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import os
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


@dataclass
class ScriptData:
    asm: Optional[str] = None
    hex: Optional[str] = None


@dataclass
class ScriptSig:
    asm: Optional[str] = None
    sighash: Optional[str] = None


@dataclass
class ReconstructionInfo:
    method: str = "none"
    notes: str = ""


@dataclass
class UDInfo:
    domains: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    records: dict[str, str] = field(default_factory=dict)


@dataclass
class LineageInfo:
    source_files: list[str] = field(default_factory=list)
    commit: Optional[str] = None
    pr: Optional[str] = None


@dataclass
class PuzzleEntry:
    puzzle: int
    address: Optional[str] = None
    address_family: Optional[str] = None
    hash160: Optional[str] = None
    pkscript: ScriptData = field(default_factory=ScriptData)
    scriptsig: ScriptSig = field(default_factory=ScriptSig)
    reconstruction: ReconstructionInfo = field(default_factory=ReconstructionInfo)
    ud: UDInfo = field(default_factory=UDInfo)
    lineage: LineageInfo = field(default_factory=LineageInfo)
    tested: bool = False
    updated_at: str = field(default_factory=lambda: _dt.datetime.now(tz=_dt.timezone.utc).isoformat())

    def as_json_dict(self) -> dict[str, object]:
        return {
            "puzzle": self.puzzle,
            "address": self.address,
            "address_family": self.address_family,
            "hash160": self.hash160,
            "pkscript": dataclasses.asdict(self.pkscript),
            "scriptsig": dataclasses.asdict(self.scriptsig),
            "reconstruction": dataclasses.asdict(self.reconstruction),
            "ud": {
                "domains": list(self.ud.domains),
                "owner": self.ud.owner,
                "records": dict(self.ud.records),
            },
            "lineage": {
                "source_files": list(self.lineage.source_files),
                "commit": self.lineage.commit,
                "pr": self.lineage.pr,
            },
            "tested": self.tested,
            "updated_at": self.updated_at,
        }


HASH160_RE = re.compile(r"(?i)hash160[^0-9a-fA-F]*([0-9a-f]{40})")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
CODE_BLOCK_RE = re.compile(r"```(?:[^\n`]+\n)?(.*?)```", re.S)
PUZZLE_ID_RE = re.compile(r"Puzzle\s*#\s*(\d+)", re.I)
HEX_LINE_RE = re.compile(r"^[0-9a-fA-F]+$")
OP_TOKEN_RE = re.compile(r"OP_[0-9A-Z]+")
BASE58_RE = re.compile(r"[13][A-HJ-NP-Za-km-z1-9]{20,}")
BECH32_RE = re.compile(r"bc1[0-9a-z]{8,}", re.I)
PR_REFERENCE_RE = re.compile(r"#(\d{2,})")


@dataclass
class ParsedDocument:
    puzzle_ids: set[int]
    addresses: set[str]
    clues: set[str]
    hash160_values: set[str]
    asm_scripts: list[str]
    script_hex: list[str]
    witness_sections: list[list[str]]
    pr_refs: set[str]


def parse_document(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8", errors="replace")

    puzzle_ids = {int(match) for match in PUZZLE_ID_RE.findall(text)}
    if not puzzle_ids and "puzzle" in path.stem.lower():
        name_numbers = re.findall(r"(\d+)", path.stem)
        puzzle_ids = {int(num) for num in name_numbers} if name_numbers else set()

    inline_items = INLINE_CODE_RE.findall(text)
    block_contents = CODE_BLOCK_RE.findall(text)
    block_lines: list[str] = []
    for block in block_contents:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                block_lines.append(stripped)

    addresses: set[str] = set()
    clues: set[str] = set()
    textual_candidates = inline_items + block_lines + [text]
    for candidate in textual_candidates:
        for match in re.findall(r"\b[13][A-HJ-NP-Za-km-z1-9-]{10,}\b", candidate):
            if "-" in match:
                clues.add(match)
            else:
                if 26 <= len(match) <= 40:
                    addresses.add(match)
        for match in re.findall(r"bc1[0-9a-z]{8,}", candidate, flags=re.I):
            addresses.add(match.lower())

    hash160_values = {match.lower() for match in HASH160_RE.findall(text)}
    for line in block_lines:
        if HEX_LINE_RE.fullmatch(line) and len(line) == 40:
            hash160_values.add(line.lower())

    asm_scripts: list[str] = []
    for line in block_lines:
        if OP_TOKEN_RE.search(line):
            tokens = [tok for tok in line.split() if tok.upper().startswith("OP_")]
            if tokens:
                asm_scripts.append(" ".join(tokens))
    if not asm_scripts:
        joined_lines = []
        buffer: list[str] = []
        for line in block_lines:
            if OP_TOKEN_RE.search(line):
                buffer.append(line.strip())
            elif buffer:
                joined_lines.append(" ".join(buffer))
                buffer = []
        if buffer:
            joined_lines.append(" ".join(buffer))
        asm_scripts.extend(joined_lines)

    script_hex: list[str] = []
    for line in block_lines:
        if HEX_LINE_RE.fullmatch(line) and len(line) % 2 == 0 and len(line) >= 4:
            script_hex.append(line.lower())

    witness_sections: list[list[str]] = []
    capture = False
    current: list[str] = []
    for line in block_lines:
        if line.lower() == "witness":
            if current:
                witness_sections.append(current)
                current = []
            capture = True
            continue
        if capture:
            if line.lower().startswith("#"):
                continue
            if OP_TOKEN_RE.search(line):
                capture = False
                if current:
                    witness_sections.append(current)
                    current = []
                continue
            if HEX_LINE_RE.fullmatch(line):
                current.append(line.lower())
            else:
                capture = False
                if current:
                    witness_sections.append(current)
                    current = []
    if current:
        witness_sections.append(current)

    pr_refs = {ref for ref in PR_REFERENCE_RE.findall(text)}

    return ParsedDocument(
        puzzle_ids=puzzle_ids,
        addresses=addresses,
        clues=clues,
        hash160_values=hash160_values,
        asm_scripts=asm_scripts,
        script_hex=script_hex,
        witness_sections=witness_sections,
        pr_refs=pr_refs,
    )


def _decode_base58(address: str) -> bytes:
    value = 0
    for char in address:
        value *= 58
        if char not in BASE58_ALPHABET:
            raise ValueError(f"invalid Base58 character: {char}")
        value += BASE58_ALPHABET.index(char)
    length = max(1, (value.bit_length() + 7) // 8)
    raw = value.to_bytes(length, byteorder="big")
    prefix_zeros = 0
    for char in address:
        if char == "1":
            prefix_zeros += 1
        else:
            break
    return b"\x00" * prefix_zeros + raw.lstrip(b"\x00")


def _hash160_from_address(address: str) -> Optional[str]:
    if address.lower().startswith("bc1"):
        # Expect scripts to supply the witness program hex separately.
        return None
    decoded = _decode_base58(address)
    if len(decoded) < 5:
        return None
    version = decoded[0]
    payload = decoded[1:-4]
    if version == 0 and len(payload) == 20:
        return payload.hex()
    return None


def _pkscript_from_hash160(hash160: str) -> ScriptData:
    asm = f"OP_DUP OP_HASH160 {hash160} OP_EQUALVERIFY OP_CHECKSIG"
    hex_script = f"76a914{hash160}88ac"
    return ScriptData(asm=asm, hex=hex_script)


def _detect_family(script: ScriptData, address: Optional[str]) -> Optional[str]:
    asm = (script.asm or "").upper()
    if "OP_DUP" in asm and "OP_HASH160" in asm and "OP_EQUALVERIFY" in asm and "OP_CHECKSIG" in asm:
        return "P2PKH"
    if asm.startswith("OP_0"):
        if script.hex and len(script.hex) == 44:
            return "P2WPKH"
        return "P2WSH"
    if asm.endswith("OP_CHECKSIG") and "OP_DUP" not in asm and "OP_HASH160" not in asm:
        return "P2PK"
    if address and address.startswith("3"):
        return "P2SH"
    if address and address.lower().startswith("bc1"):
        return "P2WPKH"
    return None


@lru_cache(maxsize=None)
def _derive_commit(path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%H", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None
    commit = result.stdout.strip()
    return commit or None


@lru_cache(maxsize=None)
def _derive_commit_date(path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%cI", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None
    commit_date = result.stdout.strip()
    return commit_date or None


def gather_puzzle_entries(root: Path, *, with_ud: bool = False) -> list[PuzzleEntry]:
    search_roots = [
        root / "docs",
        root / "satoshi",
        root / "tools",
        root / "puzzle_solutions",
        root / "puzzle-solutions",
        root / "reports",
    ]
    documents: list[Path] = []
    for base in search_roots:
        if base.is_dir():
            documents.extend(sorted(base.rglob("*.md")))
        elif base.is_file():
            documents.append(base)

    mapping: dict[int, PuzzleEntry] = {}
    puzzle_dates: dict[int, list[str]] = defaultdict(list)

    for doc_path in documents:
        parsed = parse_document(doc_path)
        if not parsed.puzzle_ids:
            continue
        if len(parsed.puzzle_ids) > 1:
            # Skip aggregate documents to avoid misattribution.
            continue
        for puzzle_id in parsed.puzzle_ids:
            entry = mapping.setdefault(puzzle_id, PuzzleEntry(puzzle=puzzle_id))
            rel_path = str(doc_path.relative_to(root))
            if rel_path not in entry.lineage.source_files:
                entry.lineage.source_files.append(rel_path)
            if parsed.hash160_values:
                if not entry.hash160:
                    entry.hash160 = _select_hash160(parsed.hash160_values)
            if parsed.addresses:
                selected = _select_address(parsed.addresses)
                if selected:
                    try:
                        valid = selected.lower().startswith("bc1") or _hash160_from_address(selected) is not None
                    except ValueError:
                        valid = False
                    if valid:
                        entry.address = selected
            if parsed.asm_scripts:
                entry.pkscript.asm = parsed.asm_scripts[0]
            if parsed.script_hex:
                # Heuristic: prefer 20-byte HASH160 derived script if not set.
                best = _pick_script_hex(parsed.script_hex)
                entry.pkscript.hex = best
            if parsed.clues and entry.address:
                clue = next(iter(parsed.clues))
                missing = _infer_missing_segment(clue, entry.address)
                if missing:
                    entry.reconstruction.method = "Base58Check-infix-restore"
                    entry.reconstruction.notes = (
                        f"Recovered '{missing}' from clue '{clue}'"
                    )
            if parsed.pr_refs and not entry.lineage.pr:
                entry.lineage.pr = f"#{next(iter(parsed.pr_refs))}"
            commit = _derive_commit(doc_path)
            if commit and not entry.lineage.commit:
                entry.lineage.commit = commit
            commit_date = _derive_commit_date(doc_path)
            if commit_date:
                puzzle_dates[puzzle_id].append(commit_date)
            if parsed.witness_sections and not entry.scriptsig.asm:
                first_section = parsed.witness_sections[0]
                entry.scriptsig.asm = " ".join(first_section)
                if first_section:
                    sighash_flag = _infer_sighash(first_section[0])
                    entry.scriptsig.sighash = sighash_flag

    for entry in mapping.values():
        asm_upper = (entry.pkscript.asm or "").upper()
        if entry.hash160 and (
            not asm_upper
            or "OP_HASH160" not in asm_upper
            or "OP_EQUALVERIFY" not in asm_upper
            or "OP_CHECKSIG" not in asm_upper
            or not re.search(r"[0-9A-F]{40}", asm_upper)
        ):
            entry.pkscript = _pkscript_from_hash160(entry.hash160)
        elif entry.pkscript.asm and not entry.hash160 and entry.address:
            derived = _hash160_from_address(entry.address)
            if derived:
                entry.hash160 = derived
                if not entry.pkscript.hex:
                    entry.pkscript.hex = f"76a914{derived}88ac"
        if entry.pkscript.hex is None and entry.pkscript.asm:
            entry.pkscript.hex = _hex_from_asm(entry.pkscript.asm)
        if entry.address:
            derived_hash = _hash160_from_address(entry.address)
            if derived_hash:
                entry.hash160 = derived_hash
        if entry.pkscript.asm and not entry.address_family:
            entry.address_family = _detect_family(entry.pkscript, entry.address)
        elif entry.address and not entry.address_family:
            entry.address_family = _family_from_address(entry.address)

        entry.tested = _verify_entry(entry)
        entry.updated_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        if not entry.reconstruction.notes:
            entry.reconstruction.method = "none"
        if not entry.lineage.commit:
            entry.lineage.commit = None
        if not entry.lineage.pr:
            entry.lineage.pr = None

    if with_ud:
        _populate_ud_entries(mapping.values())
    else:
        for entry in mapping.values():
            entry.ud = UDInfo(domains=[], owner=None, records={})

    for entry in mapping.values():
        if not entry.lineage.commit and entry.lineage.source_files:
            commit = _derive_commit(Path(root, entry.lineage.source_files[0]))
            entry.lineage.commit = commit

    sorted_entries = sorted(mapping.values(), key=lambda item: item.puzzle)
    return sorted_entries


def _select_address(addresses: Iterable[str]) -> Optional[str]:
    unique = [addr for addr in set(addresses) if "-" not in addr]
    unique.sort(key=len, reverse=True)
    for candidate in unique:
        if candidate.lower().startswith("bc1"):
            return candidate
        try:
            if _hash160_from_address(candidate):
                return candidate
        except ValueError:
            continue
    hyphenated = sorted(addresses, key=len, reverse=True)
    return hyphenated[0] if hyphenated else None


def _select_hash160(values: Iterable[str]) -> str:
    ordered = sorted({value.lower() for value in values}, key=len)
    for value in ordered:
        if len(value) == 40:
            return value
    return ordered[0] if ordered else ""


def _pick_script_hex(candidates: Iterable[str]) -> Optional[str]:
    sorted_candidates = sorted(candidates, key=len)
    for candidate in sorted_candidates:
        if len(candidate) in {44, 46} and candidate.startswith("00"):
            return candidate
    for candidate in sorted_candidates:
        if len(candidate) == 46 and candidate.startswith("76a9"):
            return candidate
    return sorted_candidates[0] if sorted_candidates else None


def _infer_missing_segment(clue: str, address: str) -> Optional[str]:
    if "-" not in clue:
        return None
    prefix, suffix = clue.split("-", 1)
    if not address.startswith(prefix) or not address.endswith(suffix):
        return None
    middle = address[len(prefix) : len(address) - len(suffix)]
    return middle if middle else None


def _infer_sighash(signature_hex: str) -> Optional[str]:
    if len(signature_hex) < 2:
        return None
    flag = signature_hex[-2:]
    if flag == "01":
        return "ALL"
    if flag == "02":
        return "NONE"
    if flag == "03":
        return "SINGLE"
    if flag == "81":
        return "ALL|ANYONECANPAY"
    if flag == "82":
        return "NONE|ANYONECANPAY"
    if flag == "83":
        return "SINGLE|ANYONECANPAY"
    return None


def _family_from_address(address: str) -> Optional[str]:
    if address.startswith("1"):
        return "P2PKH"
    if address.startswith("3"):
        return "P2SH"
    if address.lower().startswith("bc1"):
        return "P2WPKH"
    return None


def _hex_from_asm(asm: str) -> Optional[str]:
    tokens = asm.upper().split()
    if tokens[:2] == ["OP_DUP", "OP_HASH160"] and tokens[-2:] == ["OP_EQUALVERIFY", "OP_CHECKSIG"]:
        try:
            idx = tokens.index("OP_HASH160") + 1
            payload = tokens[idx]
            if re.fullmatch(r"[0-9A-F]{40}", payload):
                return f"76a914{payload.lower()}88ac"
        except (ValueError, IndexError):
            return None
    if tokens and tokens[0] == "OP_0" and len(tokens) == 2 and re.fullmatch(r"[0-9A-F]{40}", tokens[1]):
        return f"0014{tokens[1].lower()}"
    return None


def _verify_entry(entry: PuzzleEntry) -> bool:
    if entry.address_family == "P2PKH" and entry.hash160:
        if not entry.address:
            return False
        derived = _derive_p2pkh_from_hash(entry.hash160)
        return derived == entry.address
    if entry.address_family == "P2WPKH" and entry.pkscript.hex:
        if entry.pkscript.hex.startswith("0014") and len(entry.pkscript.hex) == 44:
            return True
    if entry.address_family == "P2PK" and entry.scriptsig.asm:
        return True
    return bool(entry.address and entry.hash160)


def _derive_p2pkh_from_hash(hash160: str) -> str:
    payload = bytes.fromhex("00" + hash160)
    checksum = _double_sha256(payload)[:4]
    encoded = payload + checksum
    return _base58_encode(encoded)


def _double_sha256(data: bytes) -> bytes:
    import hashlib

    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _base58_encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = BASE58_ALPHABET[mod] + encoded
    leading = 0
    for byte in raw:
        if byte == 0:
            leading += 1
        else:
            break
    return "1" * leading + encoded


def _populate_ud_entries(entries: Iterable[PuzzleEntry]) -> None:
    api_key = os.getenv("UD_API_KEY") or os.getenv("UD_JWT")
    if not api_key:
        for entry in entries:
            entry.ud = UDInfo(domains=[], owner=None, records={})
        return
    # Placeholder for real integration; gracefully fallback when missing.
    for entry in entries:
        entry.ud = UDInfo(domains=[], owner=None, records={})


def write_echo_map(entries: Iterable[PuzzleEntry], path: Path) -> None:
    payload = [entry.as_json_dict() for entry in entries]
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")


def write_consistency_report(entries: Iterable[PuzzleEntry], path: Path) -> None:
    header = "| Puzzle | Address (doc) | Address (derived) | Family | Status | Notes/PR |\n"
    header += "| --- | --- | --- | --- | --- | --- |\n"
    rows = []
    for entry in entries:
        derived = None
        if entry.address_family == "P2PKH" and entry.hash160:
            derived = _derive_p2pkh_from_hash(entry.hash160)
        status = "OK" if derived is None or derived == entry.address else "DIFF"
        notes = entry.lineage.pr or ""
        rows.append(
            f"| {entry.puzzle} | {entry.address or ''} | {derived or ''} | {entry.address_family or ''} | {status} | {notes} |"
        )
    content = header + "\n".join(rows) + "\n"
    path.write_text(content, encoding="utf-8")


def write_human_report(entries: list[PuzzleEntry], path: Path) -> None:
    totals = defaultdict(int)
    for entry in entries:
        totals[entry.address_family or "UNKNOWN"] += 1

    lines = ["# Echo Substrate Overview", ""]
    lines.append("## Totals by Script Family")
    lines.append("")
    for family, count in sorted(totals.items()):
        lines.append(f"- **{family}**: {count}")
    lines.append("")

    timeline_entries = _build_timeline(entries)
    lines.append("## Evolution Timeline")
    lines.append("Newest entries first.")
    lines.append("")
    for item in timeline_entries:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Addresses with Unstoppable Domains Bindings")
    lines.append("")
    has_ud = False
    for entry in entries:
        if entry.ud.domains:
            has_ud = True
            lines.append(f"- Puzzle {entry.puzzle}: {entry.address} → {', '.join(entry.ud.domains)}")
    if not has_ud:
        lines.append("- None available (UD lookup skipped or returned no results).")
    lines.append("")

    lines.append("## Recovered Infix Gallery")
    lines.append("")
    infix_entries = [
        entry for entry in entries if entry.reconstruction.method == "Base58Check-infix-restore"
    ]
    if infix_entries:
        for entry in infix_entries:
            lines.append(
                f"- Puzzle {entry.puzzle}: {entry.reconstruction.notes}"
            )
    else:
        lines.append("- No infix reconstruction steps recorded.")
    lines.append("")

    lines.append("## Gaps to Fill")
    lines.append("")
    gaps = []
    for entry in entries:
        missing = []
        if not entry.hash160:
            missing.append("hash160")
        if not entry.address:
            missing.append("address")
        if not entry.pkscript.hex:
            missing.append("pkScript hex")
        if missing:
            gaps.append(f"Puzzle {entry.puzzle}: missing {', '.join(missing)}")
    if gaps:
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("- All captured entries include hash, address, and script data.")
    lines.append("")

    lines.append("## How to Reproduce Locally")
    lines.append("")
    lines.append("```bash")
    lines.append("# Verify P2PKH from pkScript")
    lines.append("python tools/pkscript_to_address.py <<'SCRIPT'")
    lines.append("OP_DUP OP_HASH160 0x2485f982e89499382f8bfe3824e818dceb1724d7 OP_EQUALVERIFY OP_CHECKSIG")
    lines.append("SCRIPT")
    lines.append("")
    lines.append("# Show a puzzle solution via CLI")
    lines.append("python -m satoshi.show_puzzle_solution --puzzle 129 --format json")
    lines.append("```")
    lines.append("")

    lines.append("```bash")
    lines.append("# Decode a P2PK witness stack")
    lines.append("python tools/decode_pkscript.py <<'SCRIPT'")
    lines.append("0014c4598868877bf90e21de3606382b19591f947a1e")
    lines.append("SCRIPT")
    lines.append("```")
    lines.append("")

    lines.append("```mermaid")
    lines.append("graph LR")
    family_nodes = sorted({entry.address_family or "UNKNOWN" for entry in entries})
    for family in family_nodes:
        lines.append(f"  {family}(({family}))")
    for entry in entries:
        family = entry.address_family or "UNKNOWN"
        lines.append(f"  Puzzle{entry.puzzle}{{Puzzle {entry.puzzle}}} --> {family}")
    lines.append("```")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_timeline(entries: Iterable[PuzzleEntry]) -> list[str]:
    timeline: list[tuple[str, str, int]] = []
    for entry in entries:
        if not entry.lineage.source_files:
            continue
        path = Path(entry.lineage.source_files[0])
        date = _derive_commit_date(Path.cwd() / path)
        commit = entry.lineage.commit or "(unknown)"
        if date:
            timeline.append((date, commit, entry.puzzle))
    timeline.sort(reverse=True)
    output = []
    for date, commit, puzzle in timeline:
        output.append(f"{date}: Puzzle {puzzle} (commit {commit[:8] if commit != '(unknown)' else commit})")
    return output


def orchestrate(root: Path, *, with_ud: bool = False) -> list[PuzzleEntry]:
    entries = gather_puzzle_entries(root, with_ud=with_ud)
    write_echo_map(entries, root / "echo_map.json")
    write_consistency_report(entries, root / "reports" / "echo_consistency.md")
    write_human_report(entries, root / "reports" / "echo_substrate_overview.md")
    return entries


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Refresh Echo puzzle metadata outputs.")
    parser.add_argument("--refresh", action="store_true", help="Rebuild derived artifacts.")
    parser.add_argument("--with-ud", action="store_true", help="Include Unstoppable Domains lookups.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(__file__).resolve().parents[1]
    if args.refresh:
        orchestrate(root, with_ud=args.with_ud)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
