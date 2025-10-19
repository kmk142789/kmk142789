"""DreamCompiler transforms poetic prompts into scaffolds."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence


@dataclass(frozen=True)
class DreamPlanStep:
    """A single step in the generated plan."""

    index: int
    title: str
    description: str


@dataclass(frozen=True)
class DreamFile:
    """A file that will be written as part of the scaffold."""

    path: Path
    content: str

    def ensure_directory(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self) -> None:
        self.ensure_directory()
        self.path.write_text(self.content, encoding="utf-8")


@dataclass(frozen=True)
class DreamCompileResult:
    """Return structure for the compiler."""

    slug: str
    poem: str
    plan: Sequence[DreamPlanStep]
    files: Sequence[DreamFile]
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "poem": self.poem,
            "plan": [asdict(step) for step in self.plan],
            "files": [
                {
                    "path": str(file.path),
                    "content": file.content,
                }
                for file in self.files
            ],
            "created_at": self.created_at.isoformat(),
        }

    def export_manifest(self, target: Path) -> None:
        target.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )


class DreamCompiler:
    """Compile a poetic description into a runnable scaffold."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("state") / "dreams"

    def _slug_for(self, poem: str) -> str:
        digest = hashlib.sha256(poem.encode("utf-8")).hexdigest()[:12]
        return f"dream_{digest}"

    def _plan_for(self, poem: str) -> List[DreamPlanStep]:
        steps: List[DreamPlanStep] = []
        lines = [line.strip() for line in poem.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Poem must contain at least one non-empty line")
        for index, line in enumerate(lines, start=1):
            title = f"Weave {index}: {line[:40]}" if len(line) > 40 else f"Weave {index}: {line}"
            description = (
                "Interpret stanza as module intent and generate deterministic scaffold"
            )
            steps.append(DreamPlanStep(index=index, title=title, description=description))
        steps.append(
            DreamPlanStep(
                index=len(steps) + 1,
                title="Verify imports",
                description="Compile generated files to ensure python syntax and basic behaviour",
            )
        )
        return steps

    def _scaffold_files(self, slug: str, poem: str, plan: Sequence[DreamPlanStep]) -> List[DreamFile]:
        base = self.base_path / slug
        metadata = {
            "slug": slug,
            "poem": poem,
            "steps": [asdict(step) for step in plan],
        }
        metadata_file = DreamFile(
            path=base / "metadata.json",
            content=json.dumps(metadata, indent=2, sort_keys=True),
        )

        model_content = (
            "from __future__ import annotations\n\n"
            "from dataclasses import dataclass\n\n"
            "@dataclass(frozen=True)\n"
            "class DreamModel:\n"
            "    slug: str\n"
            "    stanza_count: int\n"
            "    created_at: str\n"
        )
        routes_content = (
            "from __future__ import annotations\n\n"
            "from fastapi import APIRouter\n\n"
            "router = APIRouter(prefix=\"/dreams\", tags=[\"dreams\"])\n\n"
            "@router.get('/{slug}')\n"
            "def show_dream(slug: str) -> dict[str, str]:\n"
            "    return {\"slug\": slug, \"message\": \"Dream weave active\"}\n"
        )
        test_content = (
            "from importlib import machinery\n\n"
            "def _module_from_path(path: str) -> None:\n"
            "    loader = machinery.SourceFileLoader('dream_model', path)\n"
            "    loader.get_code('dream_model')\n\n"
            "def test_model_compiles(tmp_path):\n"
            "    file = tmp_path / 'dream_model.py'\n"
            "    file.write_text(\"from dataclasses import dataclass\\n@dataclass\\nclass Dream: ...\", encoding='utf-8')\n"
            "    _module_from_path(str(file))\n"
        )

        files = [
            metadata_file,
            DreamFile(base / "models" / "dream_model.py", model_content + ""),
            DreamFile(base / "routes" / "dream_routes.py", routes_content + ""),
            DreamFile(base / "tests" / "test_dream_model.py", test_content + ""),
        ]
        return files

    def compile(self, poem: str, *, dry_run: bool = True) -> DreamCompileResult:
        slug = self._slug_for(poem)
        plan = self._plan_for(poem)
        files = self._scaffold_files(slug, poem, plan)
        timestamp = datetime.now(timezone.utc)
        if not dry_run:
            for file in files:
                file.write()
        return DreamCompileResult(slug=slug, poem=poem, plan=plan, files=files, created_at=timestamp)

    def diff_signature(self, result: DreamCompileResult) -> str:
        digest_parts = []
        for file in result.files:
            digest_parts.append(
                f"{file.path.name}:{hashlib.sha256(file.content.encode('utf-8')).hexdigest()}"
            )
        return "|".join(sorted(digest_parts))

    def verify_scaffold(self, result: DreamCompileResult) -> List[str]:
        issues: List[str] = []
        for file in result.files:
            try:
                compile(file.content, str(file.path), "exec")
            except SyntaxError as exc:
                issues.append(f"Syntax error in {file.path.name}: {exc}")
        return issues


__all__ = [
    "DreamCompiler",
    "DreamCompileResult",
    "DreamFile",
    "DreamPlanStep",
]
