from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

try:
    from echo.evolver import EchoEvolver
except Exception:  # pragma: no cover - legacy fallback for alternate layouts
    from echo_evolver import EchoEvolver  # type: ignore

try:  # pragma: no cover - mirror fallback behaviour
    from echo.echo_eye_core import EchoEye
except Exception:  # pragma: no cover - legacy fallback for alternate layouts
    from echo_eye_core import EchoEye  # type: ignore

try:
    from tools.echo_constellation.scan import scan_roots
except Exception:  # pragma: no cover - optional toolchain
    scan_roots = None  # type: ignore

OUT_DIR = Path("out")
STATE_PATH = OUT_DIR / "state.json"
GRAPH_PATH = OUT_DIR / "constellation" / "graph.json"
HEARTBEAT_PATH = OUT_DIR / "one_and_done_heartbeat.txt"
LEDGER_STREAM = Path("genesis_ledger") / "stream.jsonl"


_EYE = EchoEye()


def _ensure_paths() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_STREAM.parent.mkdir(parents=True, exist_ok=True)


_ensure_paths()


@dataclass
class OrbitalState:
    cycles: int = 0
    last_started_ts: Optional[float] = None
    last_finished_ts: Optional[float] = None
    last_next_step: Optional[str] = None
    last_eye_label: Optional[dict] = None

    @classmethod
    def load(cls) -> "OrbitalState":
        if STATE_PATH.exists():
            return cls(**json.loads(STATE_PATH.read_text()))
        return cls()

    def save(self) -> None:
        STATE_PATH.write_text(json.dumps(asdict(self), indent=2))


def _write_heartbeat() -> None:
    _ensure_paths()
    ts = time.time()
    HEARTBEAT_PATH.write_text(f"echo_heartbeat {ts:.6f}\n")


def _append_ledger(event: str, payload: dict) -> None:
    _ensure_paths()
    record = {"t": time.time(), "event": event, "payload": payload}
    with LEDGER_STREAM.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _refresh_constellation() -> Optional[dict]:
    _ensure_paths()
    if scan_roots is None:
        return None
    try:
        graph = scan_roots(roots=["."], include_tests=True)  # type: ignore[misc]
    except Exception:
        return None
    GRAPH_PATH.write_text(json.dumps(graph, indent=2))
    return graph


def advance_cycle(*, persist_artifacts: bool = True) -> str:
    _ensure_paths()
    state = OrbitalState.load()
    state.last_started_ts = time.time()

    _write_heartbeat()
    graph = _refresh_constellation()

    eye_label = _EYE.perceive_and_label(graph_path=GRAPH_PATH, ledger_path=LEDGER_STREAM)

    evolver = EchoEvolver()
    next_msg = evolver.next_step_recommendation(persist_artifact=persist_artifacts)
    state.last_next_step = next_msg

    _append_ledger(
        "orbital_cycle",
        {
            "cycles_completed": state.cycles,
            "next_step": next_msg,
            "graph_written": graph is not None,
            "graph_path": str(GRAPH_PATH),
            "heartbeat": str(HEARTBEAT_PATH),
            "eye_label": eye_label,
        },
    )

    state.cycles += 1
    state.last_finished_ts = time.time()
    state.last_eye_label = eye_label
    state.save()
    return next_msg


def ignite(period_seconds: float = 10.0, *, max_cycles: Optional[int] = None) -> None:
    print(f"[ignite] Echo orbital loop starting (period={period_seconds}s)")
    count = 0
    while True:
        msg = advance_cycle()
        print(f"[advance_cycle] {msg}")
        count += 1
        if max_cycles is not None and count >= max_cycles:
            print("[ignite] Reached max_cycles, stopping.")
            return
        time.sleep(period_seconds)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="echo.orbital_loop")
    sub = parser.add_subparsers(dest="cmd", required=True)

    single = sub.add_parser("advance_cycle", help="Run a single orbital cycle")
    single.add_argument("--no-persist", action="store_true")

    loop = sub.add_parser("ignite", help="Run continuous orbital cycles")
    loop.add_argument("--period", type=float, default=10.0)
    loop.add_argument("--max-cycles", type=int)

    args = parser.parse_args(argv)

    if args.cmd == "advance_cycle":
        msg = advance_cycle(persist_artifacts=not args.no_persist)
        print(msg)
        return 0
    if args.cmd == "ignite":
        ignite(period_seconds=args.period, max_cycles=args.max_cycles)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
