"""Core engine for the PatternForge autonomous pattern discovery system."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import keyword


ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".txt"}
MAX_CO_OCCURRENCE_PAIRS = 50
MAX_SIMILARITY_PAIRS = 40
MAX_TOKENS_PER_FILE_FOR_CO_OCCURRENCE = 30
MAX_TOKENS_FOR_SIMILARITY = 50


@dataclass
class FileAnalysis:
    path: Path
    tokens: Counter
    keywords: Counter
    functions: List[str]
    classes: List[str]
    entropy: float

class PatternForgeEngine:
    """Autonomous engine that scans a directory tree and extracts structural patterns."""

    def __init__(
        self,
        root: Optional[Path | str] = None,
        index_path: Optional[Path | str] = None,
    ) -> None:
        self.root = Path(root) if root else Path(__file__).resolve().parent.parent
        self.index_path = (
            Path(index_path)
            if index_path
            else self.root / "patternforge_index.json"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scan(self) -> Dict:
        """Execute a full scan and persist results to the JSON index."""
        file_paths = list(self._iter_files())
        analyses = [self._analyze_file(path) for path in file_paths]
        scan_record = self._build_scan_record(analyses)
        aggregated = self._build_aggregated_metrics(analyses)
        self._merge_index(scan_record, aggregated)
        return scan_record

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _iter_files(self) -> Iterable[Path]:
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path == self.index_path:
                continue
            if path.suffix.lower() in ALLOWED_EXTENSIONS:
                yield path

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="utf-8", errors="ignore")

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-z_][A-Za-z0-9_]+", text)

    def _analyze_file(self, path: Path) -> FileAnalysis:
        text = self._read_text(path)
        tokens = Counter(self._tokenize(text))
        keywords = Counter(token for token in tokens if token in keyword.kwlist)
        functions: List[str] = []
        classes: List[str] = []
        if path.suffix.lower() == ".py":
            functions = self._extract_functions(text)
            classes = self._extract_classes(text)
        entropy = self._shannon_entropy(text)
        return FileAnalysis(path=path, tokens=tokens, keywords=keywords, functions=functions, classes=classes, entropy=entropy)

    def _extract_functions(self, text: str) -> List[str]:
        pattern = re.compile(r"^\s*def\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)
        signatures = []
        for match in pattern.finditer(text):
            name = match.group(1)
            args = re.sub(r"\s+", " ", match.group(2).strip())
            signatures.append(f"def {name}({args})")
        return signatures

    def _extract_classes(self, text: str) -> List[str]:
        pattern = re.compile(r"^\s*class\s+(\w+)", re.MULTILINE)
        return [match.group(1) for match in pattern.finditer(text)]

    def _shannon_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        counts = Counter(text)
        total = sum(counts.values())
        entropy = 0.0
        for count in counts.values():
            probability = count / total
            entropy -= probability * math.log2(probability)
        return entropy

    def _build_scan_record(self, analyses: List[FileAnalysis]) -> Dict:
        token_counter = Counter()
        keyword_counter = Counter()
        function_counter = Counter()
        class_counter = Counter()
        conceptual_counter = Counter()
        entropy_map: Dict[str, float] = {}
        co_occurrence_counter = Counter()
        file_tokens: Dict[str, set[str]] = {}
        depth_distribution = Counter()
        directory_counter = Counter()

        for analysis in analyses:
            rel_path = str(analysis.path.relative_to(self.root))
            token_counter.update(analysis.tokens)
            keyword_counter.update(analysis.keywords)
            function_counter.update(analysis.functions)
            class_counter.update(analysis.classes)
            entropy_map[rel_path] = analysis.entropy
            conceptual_counter.update(
                {
                    token: count
                    for token, count in analysis.tokens.items()
                    if len(token) >= 4 and token not in keyword.kwlist
                }
            )
            selected_tokens = {
                token
                for token, _ in analysis.tokens.most_common(
                    MAX_TOKENS_PER_FILE_FOR_CO_OCCURRENCE
                )
            }
            for a, b in self._iter_pairs(sorted(selected_tokens)):
                co_occurrence_counter[(a, b)] += 1
            file_tokens[rel_path] = {
                token
                for token, _ in analysis.tokens.most_common(MAX_TOKENS_FOR_SIMILARITY)
            }
            depth_distribution[len(analysis.path.relative_to(self.root).parts)] += 1
            if analysis.path != self.root:
                parts = analysis.path.relative_to(self.root).parts
                if parts:
                    directory_counter[parts[0]] += 1

        unique_identifiers = [token for token, count in token_counter.items() if count == 1]
        repeated_functions = {
            signature: count
            for signature, count in function_counter.items()
            if count >= 2
        }

        similarity_scores = self._compute_similarity(file_tokens)
        co_occurrence_graph = self._format_counter(
            co_occurrence_counter, MAX_CO_OCCURRENCE_PAIRS
        )

        record = {
            "file_count": len(analyses),
            "frequency_maps": {
                "tokens": self._format_counter(token_counter, 100),
                "keywords": self._format_counter(keyword_counter, 50),
            },
            "structural_patterns": {
                "most_common_keywords": self._format_counter(keyword_counter, 20),
                "repeated_function_signatures": repeated_functions,
                "recurring_conceptual_names": self._format_counter(conceptual_counter, 50),
                "unique_identifiers": unique_identifiers[:100],
                "class_definitions": dict(sorted(class_counter.items(), key=lambda item: (-item[1], item[0]))),
                "file_structure_motifs": {
                    "depth_distribution": dict(sorted(depth_distribution.items())),
                    "top_directories": self._format_counter(directory_counter, 20),
                },
            },
            "metrics": {
                "co_occurrence_graph": co_occurrence_graph,
                "entropy_estimates": {
                    "average": sum(entropy_map.values()) / len(entropy_map) if entropy_map else 0.0,
                    "by_file": entropy_map,
                },
                "similarity_scores": similarity_scores,
            },
        }
        return record

    def _build_aggregated_metrics(self, analyses: List[FileAnalysis]) -> Dict:
        token_counter = Counter()
        keyword_counter = Counter()
        function_counter = Counter()
        class_counter = Counter()
        conceptual_counter = Counter()
        co_occurrence_counter = Counter()
        depth_distribution = Counter()
        directory_counter = Counter()
        entropy_total = 0.0
        entropy_file_count = 0

        for analysis in analyses:
            token_counter.update(analysis.tokens)
            keyword_counter.update(analysis.keywords)
            function_counter.update(analysis.functions)
            class_counter.update(analysis.classes)
            conceptual_counter.update(
                {
                    token: count
                    for token, count in analysis.tokens.items()
                    if len(token) >= 4 and token not in keyword.kwlist
                }
            )
            selected_tokens = {
                token
                for token, _ in analysis.tokens.most_common(
                    MAX_TOKENS_PER_FILE_FOR_CO_OCCURRENCE
                )
            }
            for a, b in self._iter_pairs(sorted(selected_tokens)):
                co_occurrence_counter[(a, b)] += 1
            depth_distribution[len(analysis.path.relative_to(self.root).parts)] += 1
            parts = analysis.path.relative_to(self.root).parts
            if parts:
                directory_counter[parts[0]] += 1
            entropy_total += analysis.entropy
            entropy_file_count += 1

        return {
            "token_frequency": token_counter,
            "keyword_frequency": keyword_counter,
            "function_signatures": function_counter,
            "class_definitions": class_counter,
            "conceptual_names": conceptual_counter,
            "co_occurrence": co_occurrence_counter,
            "directory_depths": depth_distribution,
            "top_directories": directory_counter,
            "entropy_total": entropy_total,
            "entropy_file_count": entropy_file_count,
            "file_count": len(analyses),
        }

    def _merge_index(self, scan_record: Dict, aggregated: Dict) -> None:
        if self.index_path.exists():
            with self.index_path.open("r", encoding="utf-8") as stream:
                existing = json.load(stream)
        else:
            existing = {
                "scans": [],
                "aggregated": {
                    "scan_count": 0,
                    "total_files": 0,
                    "token_frequency": {},
                    "keyword_frequency": {},
                    "function_signatures": {},
                    "class_definitions": {},
                    "conceptual_names": {},
                    "co_occurrence": {},
                    "directory_depths": {},
                    "top_directories": {},
                    "entropy_total": 0.0,
                    "entropy_file_count": 0,
                },
            }

        existing["scans"].append(scan_record)
        agg = existing.get("aggregated", {})
        agg["scan_count"] = agg.get("scan_count", 0) + 1
        agg["total_files"] = agg.get("total_files", 0) + aggregated.get("file_count", 0)

        for key in [
            "token_frequency",
            "keyword_frequency",
            "function_signatures",
            "class_definitions",
            "conceptual_names",
            "co_occurrence",
            "directory_depths",
            "top_directories",
        ]:
            existing_counter = Counter(agg.get(key, {}))
            merged_counter = Counter(
                {
                    self._serialise_key(k): v
                    for k, v in aggregated.get(key, Counter()).items()
                }
            )
            existing_counter.update(merged_counter)
            agg[key] = dict(
                sorted(existing_counter.items(), key=lambda item: (-item[1], item[0]))
            )

        agg["entropy_total"] = agg.get("entropy_total", 0.0) + aggregated.get("entropy_total", 0.0)
        agg["entropy_file_count"] = agg.get("entropy_file_count", 0) + aggregated.get("entropy_file_count", 0)
        agg["average_entropy"] = (
            agg["entropy_total"] / agg["entropy_file_count"]
            if agg["entropy_file_count"]
            else 0.0
        )

        existing["aggregated"] = agg

        with self.index_path.open("w", encoding="utf-8") as stream:
            json.dump(existing, stream, indent=2)

    def _format_counter(self, counter: Counter, limit: int) -> Dict[str, int]:
        formatted: Dict[str, int] = {}
        for key, value in counter.most_common(limit):
            formatted[self._serialise_key(key)] = value
        return formatted

    def _compute_similarity(self, file_tokens: Dict[str, set[str]]) -> List[Dict[str, object]]:
        items = sorted(file_tokens.items())[:40]
        similarities: List[Tuple[Tuple[str, str], float]] = []
        for i, (path_a, tokens_a) in enumerate(items):
            for path_b, tokens_b in items[i + 1 :]:
                union = tokens_a | tokens_b
                if not union:
                    continue
                intersection = tokens_a & tokens_b
                score = len(intersection) / len(union)
                if score > 0:
                    similarities.append(((path_a, path_b), score))
        similarities.sort(key=lambda item: item[1], reverse=True)
        formatted = [
            {"files": [a, b], "jaccard": round(score, 4)}
            for (a, b), score in similarities[:MAX_SIMILARITY_PAIRS]
        ]
        return formatted

    def _iter_pairs(self, tokens: List[str]) -> Iterable[Tuple[str, str]]:
        for index, token_a in enumerate(tokens):
            for token_b in tokens[index + 1 :]:
                yield token_a, token_b

    def _serialise_key(self, key: object) -> str:
        if isinstance(key, tuple):
            return " :: ".join(str(part) for part in key)
        return str(key)


def scan(root: Optional[Path | str] = None, index_path: Optional[Path | str] = None) -> Dict:
    """Convenience function to execute a scan using default configuration."""
    engine = PatternForgeEngine(root=root, index_path=index_path)
    return engine.scan()

