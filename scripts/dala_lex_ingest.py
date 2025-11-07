#!/usr/bin/env python3
"""Utilities for ingesting legal authorities into the DALA Lexicon."""

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import textwrap

LEXICON_PATH = Path("packages/dala-lex/lexicon.json")
CHANGELOG_PATH = Path("packages/dala-lex/CHANGELOG.md")
BASE_PATH = Path("packages/dala-lex")
DOMAINS = {
    "governance": "Governance & Oversight",
    "fiduciary": "Fiduciary Duties & Financial Integrity",
    "privacy": "Data Protection & Privacy Operations",
    "cross-border": "Cross-Border & Jurisdictional Alignment",
}
CATEGORY_DIRS = {
    "precedent": BASE_PATH / "precedents",
    "regulatory_update": BASE_PATH / "regulatory_updates",
    "accreditation": BASE_PATH / "accreditation",
}


def load_lexicon() -> dict:
    if not LEXICON_PATH.exists():
        raise FileNotFoundError("lexicon.json not found. Run from repository root.")
    with LEXICON_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_lexicon(data: dict) -> None:
    data["generated_at"] = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with LEXICON_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=False)
        handle.write("\n")


def increment_version(version: str) -> str:
    major, minor, patch = version.split(".")
    patch = str(int(patch) + 1)
    return ".".join([major, minor, patch])


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def infer_domains(text: str) -> list[str]:
    lower_text = text.lower()
    mapping = {
        "governance": DOMAINS["governance"],
        "board": DOMAINS["governance"],
        "fiduciary": DOMAINS["fiduciary"],
        "treasury": DOMAINS["fiduciary"],
        "capital": DOMAINS["fiduciary"],
        "privacy": DOMAINS["privacy"],
        "data": DOMAINS["privacy"],
        "gdpr": DOMAINS["privacy"],
        "cross-border": DOMAINS["cross-border"],
        "international": DOMAINS["cross-border"],
        "sanctions": DOMAINS["cross-border"],
        "jurisdiction": DOMAINS["cross-border"],
    }
    domains = []
    for keyword, domain in mapping.items():
        if keyword in lower_text and domain not in domains:
            domains.append(domain)
    if not domains:
        domains.append("General compliance review required")
    return domains


def summarize_text(text: str, max_sentences: int = 3) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    summary = " ".join(sentences[:max_sentences])
    wrapped = textwrap.fill(summary, width=100)
    return wrapped


def write_entry(category: str, entry_id: str, payload: dict) -> Path:
    target_dir = CATEGORY_DIRS[category]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{entry_id}.json"
    with target_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return target_path


def append_changelog(entry_id: str, title: str, category: str) -> None:
    timestamp = dt.datetime.utcnow().date().isoformat()
    line = f"- {timestamp}: Added {category.replace('_', ' ')} `{entry_id}` — {title}"
    existing = CHANGELOG_PATH.read_text(encoding="utf-8").strip()
    if "## [Unreleased]" not in existing:
        updated = existing + "\n\n## [Unreleased]\n" + line + "\n"
    else:
        updated = re.sub(r"(## \[Unreleased\]\n)", r"\\1" + line + "\n", existing, count=1)
    with CHANGELOG_PATH.open("w", encoding="utf-8") as handle:
        handle.write(updated + "\n")


def register_entry(args: argparse.Namespace) -> Path:
    lexicon = load_lexicon()
    category_key = {
        "precedent": "precedents",
        "regulatory_update": "regulatory_updates",
        "accreditation": "accreditation",
    }[args.category]

    text = Path(args.source_file).read_text(encoding="utf-8")
    domains = infer_domains(text)
    summary = summarize_text(text)
    entry_id = f"{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{slugify(args.title)}"
    payload = {
        "id": entry_id,
        "title": args.title,
        "category": args.category,
        "effective_date": args.effective_date,
        "source_file": str(Path(args.source_file).resolve()),
        "annotated_domains": domains,
        "summary": summary,
        "accreditation_notes": args.accreditation_notes or "Automated annotation",
        "ingested_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    artifact_path = write_entry(args.category, entry_id, payload)

    lexicon["entries"][category_key].append(payload)
    lexicon["version"] = increment_version(lexicon["version"])
    save_lexicon(lexicon)
    append_changelog(entry_id, args.title, args.category)
    return artifact_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", required=True, help="Path to the text or markdown file to ingest")
    parser.add_argument("--title", required=True, help="Short title for the authority or update")
    parser.add_argument(
        "--category",
        required=True,
        choices=sorted(CATEGORY_DIRS.keys()),
        help="Type of entry being ingested",
    )
    parser.add_argument(
        "--effective-date",
        required=True,
        help="Effective date for the authority in ISO format (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--accreditation-notes",
        required=False,
        help="Optional manual annotation describing accreditation impact",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    artifact_path = register_entry(args)
    print(f"Registered {args.category} entry: {artifact_path}")


if __name__ == "__main__":
    main()
