"""Utilities for parsing simple BIND-style DNS zone files.

This module focuses on the subset of records we frequently archive in the Echo
repositories: SOA, NS, A/AAAA, CNAME, MX and TXT entries.  The parser is
purposefully light-weight so it can run without external dependencies or
network access.  It strips inline comments, normalises whitespace and exposes a
small dataclass representing each record.

Example
-------
>>> from tools.dns_zone_parser import parse_zone_text, summarise_records
>>> text = "\n".join([
...     "btcpuzzle.info\t3600\tIN\tSOA\tbrian.ns.cloudflare.com. dns.cloudflare.com. 2051308780 10000 2400 604800 3600",
...     "btcpuzzle.info.\t86400\tIN\tNS\tbrian.ns.cloudflare.com.",
... ])
>>> records = parse_zone_text(text)
>>> records[0].rtype
'SOA'
>>> summary = summarise_records(records)
>>> summary['total_records']
2

The helper intentionally performs only minimal validation so it can ingest
partial zone exports or redacted datasets.  Unknown record classes and types are
still captured — they simply pass through to the ``DNSRecord`` dataclass.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


@dataclass(frozen=True)
class DNSRecord:
    """Representation of a single DNS record extracted from a zone file."""

    name: str
    ttl: int | None
    rclass: str
    rtype: str
    value: str

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "name": self.name,
            "ttl": self.ttl,
            "class": self.rclass,
            "type": self.rtype,
            "value": self.value,
        }


def _strip_comment(line: str) -> str:
    """Remove inline comments while honouring quoted and escaped semicolons."""

    cleaned: List[str] = []
    in_quotes = False
    escaped = False

    for char in line:
        if escaped:
            cleaned.append(char)
            escaped = False
            continue

        if char == "\\":
            cleaned.append(char)
            escaped = True
            continue

        if char == '"':
            cleaned.append(char)
            in_quotes = not in_quotes
            continue

        if char == ";" and not in_quotes:
            break

        cleaned.append(char)

    return "".join(cleaned).strip()


def _tokenise(line: str) -> Sequence[str]:
    """Split a zone file line into tokens while preserving quoted strings."""

    tokens: List[str] = []
    current: List[str] = []
    in_quotes = False
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
            current.append(char)
            continue
        if char.isspace() and not in_quotes:
            if current:
                tokens.append("".join(current))
                current = []
            continue
        current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def _parse_tokens(tokens: Sequence[str], previous_name: str | None) -> tuple[DNSRecord, str]:
    if not tokens:
        raise ValueError("cannot parse empty token sequence")

    name = tokens[0]
    if name in {"@", ""}:
        if previous_name is None:
            raise ValueError("zone uses implicit owner name before any record defined")
        name = previous_name

    ttl: int | None = None
    index = 1
    if index < len(tokens) and tokens[index].isdigit():
        ttl = int(tokens[index])
        index += 1

    if index >= len(tokens):
        raise ValueError("record missing class/type information")

    rclass = tokens[index]
    if rclass.upper() not in {"IN", "CH", "HS"}:
        rtype = rclass
        rclass = "IN"
    else:
        index += 1
        if index >= len(tokens):
            raise ValueError("record missing type information")
        rtype = tokens[index]

    if index + 1 >= len(tokens):
        value_tokens: Sequence[str] = []
    else:
        value_tokens = tokens[index + 1 :]

    value = " ".join(value_tokens).strip()
    record = DNSRecord(name=name, ttl=ttl, rclass=rclass.upper(), rtype=rtype.upper(), value=value)
    return record, name


def parse_zone_lines(lines: Iterable[str]) -> List[DNSRecord]:
    """Parse the supplied zone file lines."""

    records: List[DNSRecord] = []
    previous_name: str | None = None
    for raw_line in lines:
        cleaned = _strip_comment(raw_line)
        if not cleaned:
            continue
        tokens = _tokenise(cleaned)
        if not tokens:
            continue
        record, previous_name = _parse_tokens(tokens, previous_name)
        records.append(record)
    return records


def parse_zone_text(text: str) -> List[DNSRecord]:
    """Parse a zone file payload provided as text."""

    return parse_zone_lines(text.splitlines())


def summarise_records(records: Sequence[DNSRecord]) -> dict[str, object]:
    """Return aggregate information about the supplied records."""

    counts: dict[str, int] = {}
    ttls: List[int] = []
    hosts: set[str] = set()
    txt_values: List[str] = []

    for record in records:
        counts[record.rtype] = counts.get(record.rtype, 0) + 1
        if record.ttl is not None:
            ttls.append(record.ttl)
        hosts.add(record.name)
        if record.rtype == "TXT":
            txt_values.append(record.value)

    ttl_summary = None
    if ttls:
        ttl_summary = {"min": min(ttls), "max": max(ttls), "unique": sorted(set(ttls))}

    return {
        "total_records": len(records),
        "record_types": counts,
        "ttl_summary": ttl_summary,
        "host_count": len(hosts),
        "hosts": sorted(hosts),
        "txt_records": txt_values,
    }


def _iter_cli_records(path: Path) -> Iterator[DNSRecord]:
    text = path.read_text(encoding="utf-8")
    yield from parse_zone_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zone", type=Path, help="Path to the zone file to parse.")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to emit a JSON summary containing the records and aggregates.",
    )
    parser.add_argument(
        "--records",
        action="store_true",
        help="Print the parsed records as JSON to stdout instead of the summary.",
    )
    args = parser.parse_args()

    records = list(_iter_cli_records(args.zone))
    summary = summarise_records(records)

    if args.records:
        print(json.dumps([record.as_dict() for record in records], indent=2))
    else:
        print(json.dumps(summary, indent=2))

    if args.json:
        payload = {
            "summary": summary,
            "records": [record.as_dict() for record in records],
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
