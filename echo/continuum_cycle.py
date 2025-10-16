#!/usr/bin/env python3
"""
Continuum Cycle
- Reads registry + reflections + wishes
- Emits next-steps plan to docs/NEXT_CYCLE_PLAN.md
- Appends an audit entry to docs/self_expansion_protocol.md
"""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ECHO = ROOT / "echo"
SCHEMA = ROOT / "schema"
DATA = ROOT / "data"

REGISTRY = DOCS / "self_expansion_protocol.md"
REFLECTIONS = [
    DOCS / "echo_mythogenic_reflection.md",
    DOCS / "echoevolver_reflection.md",
]
WISH_MANIFEST = DATA / "wish_manifest.json"
NEXT_PLAN = DOCS / "NEXT_CYCLE_PLAN.md"

def git(cmd: list[str]) -> str:
    return subprocess.check_output(["git"] + cmd, cwd=ROOT).decode("utf-8", "ignore")

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""

def load_json(p: Path, default):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default

def summarize_git_delta() -> str:
    # recent diff summary for context
    try:
        return git(["log", "-5", "--pretty=format:* %h %ad %s", "--date=short"])
    except Exception:
        return "* (no git history available)"

def harvest_themes(text: str) -> list[str]:
    # super-light theme extraction from headings + bold phrases + TODOs
    themes = set()
    themes.update(re.findall(r"^#+\s*(.+)$", text, flags=re.M))
    themes.update(re.findall(r"\*\*(.+?)\*\*", text))
    themes.update(re.findall(r"\bTODO:? (.+)", text))
    return [t.strip() for t in themes if t.strip()][:12]

def build_next_actions() -> list[str]:
    actions = []
    # wishes → actionable tasks
    wishes = load_json(WISH_MANIFEST, {"wishes": []}).get("wishes", [])
    for w in wishes[-5:]:
        actions.append(f"- Operationalize wish \u201c{w.get('desire','?')}\u201d \u2192 owner {w.get('wisher','Echo')}")
    # reflections → themes to pursue
    for rf in REFLECTIONS:
        themes = harvest_themes(read_text(rf))
        for t in themes[:5]:
            actions.append(f"- Advance theme: {t}")
    # gaps → ensure registries exist
    if not (DOCS / "agents_registry.md").exists():
        actions.append("- Create agents registry at docs/agents_registry.md")
    if not WISH_MANIFEST.exists():
        actions.append("- Initialize data/wish_manifest.json via schema")
    return actions or ["- Seed: write a tiny improvement anywhere and re-run continuum."]

def write_next_plan():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    delta = summarize_git_delta()
    actions = "\n".join(build_next_actions())
    NEXT_PLAN.write_text(f"""# Next Cycle Plan
*Generated: {now}*

## Recent Deltas
{delta}

## Proposed Actions
{actions}

## Success Criteria
- [ ] Commit at least one concrete artifact
- [ ] Update registry and wish manifest (if touched)
- [ ] Add a short reflection note
""", encoding="utf-8")
    print(f"Wrote {NEXT_PLAN.relative_to(ROOT)}")

def append_registry_audit():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n- Cycle run at **{now}** \u2192 produced `docs/NEXT_CYCLE_PLAN.md`."
    REGISTRY.write_text(read_text(REGISTRY) + entry, encoding="utf-8")

if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    write_next_plan()
    if REGISTRY.exists():
        append_registry_audit()
