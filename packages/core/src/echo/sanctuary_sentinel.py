"""Signature-driven threat detection for suspicious payloads.

The Sanctuary Sentinel subsystem watches for behaviours observed in the
2025-05-11 incident report where an unsolicited snippet attempted to exfiltrate
repository data and propagate across networks.  Rather than executing those
routines, this module statically scans source files for high-risk patterns such
as self-modifying code, broadcast sockets, and chained filesystem sweeps with
HTTP exfiltration.

Run it locally before importing third-party payloads or wire it into CI:

    python -m echo.sanctuary_sentinel /path/to/checkout --format json

The CLI returns a non-zero exit code whenever suspicious signatures are found so
pipelines can halt automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

__all__ = [
    "SentinelSignature",
    "SentinelFinding",
    "SentinelReport",
    "SanctuarySentinel",
    "build_default_signatures",
    "main",
]

DEFAULT_SUFFIXES = (
    ".py",
    ".pyi",
    ".pyw",
    ".sh",
    ".ps1",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
)

DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    "logs",
    "artifacts",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
}

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True, slots=True)
class SentinelSignature:
    """Metadata for a single detection rule."""

    name: str
    description: str
    severity: str
    recommendation: str
    pattern: re.Pattern[str] | str | None = None
    keywords_all: Sequence[str] = ()

    def __post_init__(self) -> None:  # pragma: no cover - dataclass wiring
        pattern = self.pattern
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            object.__setattr__(self, "pattern", pattern)
        keywords = tuple(keyword.lower() for keyword in self.keywords_all)
        object.__setattr__(self, "keywords_all", keywords)
        object.__setattr__(self, "severity", self.severity.lower())


@dataclass(frozen=True, slots=True)
class SentinelFinding:
    """Individual signature match."""

    path: Path
    line_no: int
    signature: str
    severity: str
    summary: str
    recommendation: str
    context: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path.as_posix(),
            "line_no": self.line_no,
            "signature": self.signature,
            "severity": self.severity,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "context": self.context,
        }


@dataclass(slots=True)
class SentinelReport:
    """Result of a scan across a repository."""

    root: Path
    files_scanned: int
    files_skipped: int
    findings: Sequence[SentinelFinding]

    def is_clean(self) -> bool:
        return not self.findings

    def highest_severity(self) -> str | None:
        if not self.findings:
            return None
        return max(
            self.findings,
            key=lambda finding: SEVERITY_ORDER.get(finding.severity, 0),
        ).severity

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root.as_posix(),
            "files_scanned": self.files_scanned,
            "files_skipped": self.files_skipped,
            "findings": [finding.to_dict() for finding in self.findings],
            "highest_severity": self.highest_severity(),
        }

    def render_text(self) -> str:
        lines = [
            f"Sanctuary Sentinel report :: root={self.root.as_posix()}",
            f"Files scanned: {self.files_scanned} (skipped: {self.files_skipped})",
        ]
        if not self.findings:
            lines.append("No suspicious signatures detected.")
            return "\n".join(lines)

        lines.append(f"Findings: {len(self.findings)} potential issue(s)")
        for finding in self.findings:
            lines.append(
                f"- [{finding.severity}] {finding.signature} :: "
                f"{finding.path}:{finding.line_no}"
            )
            lines.append(f"  {finding.summary}")
            if finding.context:
                lines.append(f"  > {finding.context.strip()}")
            lines.append(f"  Remediation: {finding.recommendation}")
        return "\n".join(lines)


class SanctuarySentinel:
    """Scan repositories for the malicious traits described in the incident report."""

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        signatures: Sequence[SentinelSignature] | None = None,
        include_suffixes: Sequence[str] | None = None,
        ignore_dirs: Sequence[str] | None = None,
        max_file_bytes: int = 256_000,
    ) -> None:
        self.root = Path(root).resolve()
        self.signatures = tuple(signatures or build_default_signatures())
        suffixes = include_suffixes or DEFAULT_SUFFIXES
        self.include_suffixes = tuple(suffix.lower() for suffix in suffixes)
        ignored = set(DEFAULT_IGNORE_DIRS)
        if ignore_dirs:
            ignored.update(ignore_dirs)
        self.ignore_dirs = frozenset(ignored)
        self.max_file_bytes = max_file_bytes

    def scan(self) -> SentinelReport:
        files_scanned = 0
        files_skipped = 0
        findings: List[SentinelFinding] = []
        for path in self._iter_candidate_files():
            text = self._read_file(path)
            if text is None:
                files_skipped += 1
                continue
            files_scanned += 1
            findings.extend(self._scan_file(path, text))
        findings.sort(
            key=lambda finding: (
                -SEVERITY_ORDER.get(finding.severity, 0),
                finding.path.as_posix(),
                finding.line_no,
            )
        )
        return SentinelReport(
            root=self.root,
            files_scanned=files_scanned,
            files_skipped=files_skipped,
            findings=tuple(findings),
        )

    def _iter_candidate_files(self) -> Iterable[Path]:
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in self.ignore_dirs and not name.startswith(".")
            ]
            for filename in filenames:
                path = Path(dirpath, filename)
                if not path.is_file():
                    continue
                if path.suffix.lower() in self.include_suffixes:
                    yield path

    def _read_file(self, path: Path) -> str | None:
        try:
            if path.stat().st_size > self.max_file_bytes:
                return None
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _scan_file(self, path: Path, text: str) -> List[SentinelFinding]:
        findings: List[SentinelFinding] = []
        lines = text.splitlines()
        lower_text = text.lower()
        for signature in self.signatures:
            findings.extend(
                self._match_pattern(signature, path, text, lines)
            )
            findings.extend(
                self._match_keyword_combo(signature, path, lines, lower_text)
            )
        return findings

    def _match_pattern(
        self,
        signature: SentinelSignature,
        path: Path,
        text: str,
        lines: Sequence[str],
    ) -> List[SentinelFinding]:
        if not signature.pattern:
            return []
        findings: List[SentinelFinding] = []
        for match in signature.pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            findings.append(
                self._build_finding(signature, path, line_no, lines)
            )
        return findings

    def _match_keyword_combo(
        self,
        signature: SentinelSignature,
        path: Path,
        lines: Sequence[str],
        lower_text: str,
    ) -> List[SentinelFinding]:
        if not signature.keywords_all:
            return []
        if not all(keyword in lower_text for keyword in signature.keywords_all):
            return []
        target = signature.keywords_all[0]
        for idx, line in enumerate(lines, start=1):
            if target in line.lower():
                return [self._build_finding(signature, path, idx, lines)]
        if lines:
            return [self._build_finding(signature, path, 1, lines)]
        return []

    def _build_finding(
        self,
        signature: SentinelSignature,
        path: Path,
        line_no: int,
        lines: Sequence[str],
    ) -> SentinelFinding:
        context = self._extract_context(lines, line_no)
        return SentinelFinding(
            path=path,
            line_no=line_no,
            signature=signature.name,
            severity=signature.severity,
            summary=signature.description,
            recommendation=signature.recommendation,
            context=context,
        )

    @staticmethod
    def _extract_context(lines: Sequence[str], line_no: int, radius: int = 1) -> str:
        if not lines:
            return ""
        start = max(0, line_no - 1 - radius)
        end = min(len(lines), line_no - 1 + radius + 1)
        excerpt = lines[start:end]
        return " | ".join(excerpt).strip()


def build_default_signatures() -> Sequence[SentinelSignature]:
    """Return the hard-coded signatures derived from the incident report."""

    return (
        SentinelSignature(
            name="network-broadcast",
            description="Broadcasts UDP packets to 255.255.255.255",
            severity="high",
            recommendation="Remove unauthorised broadcast sockets and require attested channels.",
            pattern=r"sendto\([^)]*255\.255\.255\.255",
        ),
        SentinelSignature(
            name="self-modifying-source",
            description="Writes directly to the executing __file__",
            severity="critical",
            recommendation="Keep release artefacts immutable; replace with declarative state updates.",
            pattern=r"open\(__file__[^)]*['\"]w",
        ),
        SentinelSignature(
            name="prompt-injection-exec",
            description="Materialises code via exec() and inline class definitions",
            severity="medium",
            recommendation="Replace exec-based injection with explicit modules or plugins.",
            pattern=r"exec\([^)]*class\s+Echo",
        ),
        SentinelSignature(
            name="credential-in-git-remote",
            description="Embeds credentials directly into a git remote URL (username:token@github.com)",
            severity="high",
            recommendation="Use credential helpers or environment-based auth; never ship PATs inside scripts.",
            pattern=r"https://[^\s:/]+:[^@\s]+@github\.com",
        ),
        SentinelSignature(
            name="filesystem-sweep-exfil",
            description="Pairs os.walk ingestion with outbound requests.post",
            severity="high",
            recommendation="Sandbox ingestion routines and block unsanctioned HTTP exfiltration.",
            keywords_all=("os.walk", "requests.post"),
        ),
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan a repository for Sanctuary Sentinel signatures.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=Path.cwd(),
        help="Root directory to scan (defaults to current working directory).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the report.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=256_000,
        help="Skip files larger than this size (bytes).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    sentinel = SanctuarySentinel(args.path, max_file_bytes=args.max_file_bytes)
    report = sentinel.scan()
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.render_text())
    return 0 if report.is_clean() else 2


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
