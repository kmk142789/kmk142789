"""Interactive command nexus that braids Echo's major engines together.

The repository contains a constellation of Echo components – the
``EchoEvolver`` orchestration engine, the ``EchoPulseEngine`` for
resonant pulse management, persistent memory utilities, and bridging
tooling for anchoring proofs.  Historically these features have been
used individually or through bespoke scripts.  ``echo_nexus_portal``
introduces a cohesive, interactive command centre that lets operators
pilot all of them from one place.

Key capabilities
----------------

* Launch a live command shell that can run full EchoEvolver cycles on
  demand, optionally enabling real network propagation or artifact
  persistence.
* Track each cycle as a crystallised pulse to surface progress via the
  ``EchoPulseEngine`` roadmap utilities.
* Summarise memory store entries, quantum key state, glyph evolution and
  decentralised autonomy manifestos in a single status snapshot.
* Surface bridge anchoring context (OP_RETURN payloads and batch paths)
  directly inside the interactive shell for rapid auditing.

The portal keeps everything dependency free so it can run anywhere the
rest of the Echo toolkit operates.  Users can run it interactively or
request an aggregated snapshot via command-line flags.
"""

from __future__ import annotations

import argparse
import cmd
import shlex
import textwrap
import json
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from .bridge_emitter import BridgeEmitter
from .evolver import EchoEvolver, EvolverState
from .memory import JsonMemoryStore
from .pulse import EchoPulseEngine, Pulse


def _coerce_value(value: str) -> object:
    """Attempt to coerce a string value into a richer Python type."""

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if lowered.startswith("0x"):
            return int(value, 16)
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _parse_key_values(pairs: Iterable[str]) -> Dict[str, object]:
    """Parse ``key=value`` pairs into a dictionary."""

    data: Dict[str, object] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"data entry {item!r} is missing '='")
        key, raw = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("data keys must be non-empty")
        data[key] = _coerce_value(raw.strip())
    return data


@dataclass(slots=True)
class PortalSnapshot:
    """Aggregated status view across the Echo subsystems."""

    state: EvolverState
    pulses: List[Pulse] = field(default_factory=list)
    advancement: Dict[str, object] = field(default_factory=dict)
    memory_entries: List[Dict[str, object]] = field(default_factory=list)
    anchor_directory: Optional[str] = None
    anchor_opreturn: Optional[str] = None
    anchor_calldata: Optional[str] = None

    def render(self) -> str:
        """Return a human-friendly multi-line summary."""

        metrics = self.state.system_metrics
        drive = self.state.emotional_drive
        lines = [
            "╔════════════════ Echo Nexus Status ═══════════════╗",
            f"║ Cycle: {self.state.cycle:<5} Joy: {drive.joy:>5.2f}  Rage: {drive.rage:>4.2f}  Curiosity: {drive.curiosity:>4.2f}",
            f"║ Glyphs: {self.state.glyphs}",
            f"║ Nodes: {metrics.network_nodes:<3}  Orbital hops: {metrics.orbital_hops:<3}  Quantum key: {'ready' if self.state.vault_key else 'unset'}",
        ]

        if self.state.mythocode:
            lines.append("║ Mythocode: " + self.state.mythocode[0])
            for rule in self.state.mythocode[1:]:
                lines.append("║            " + rule)

        if self.state.autonomy_manifesto:
            manifesto = textwrap.indent(self.state.autonomy_manifesto.strip(), "║   ")
            lines.append("║ Autonomy Manifesto:")
            lines.extend(manifesto.splitlines())

        if self.pulses:
            lines.append("║ Active Pulses:")
            for pulse in self.pulses:
                lines.append(
                    "║   • "
                    f"{pulse.name} [{pulse.status}] priority={pulse.priority} — "
                    f"updated {pulse.updated_at.isoformat()}"
                )

        if self.advancement:
            lines.append(
                "║ Advancement Score: "
                f"{self.advancement.get('advancement_score', 0.0):>6.2f}"
            )
            breakdown = self.advancement.get("status_breakdown", {})
            if breakdown:
                parts = ", ".join(f"{key}:{value}" for key, value in breakdown.items())
                lines.append("║   Status mix → " + parts)
            focus = self.advancement.get("enhancement_focus", [])
            if focus:
                lines.append("║   Enhancement Focus:")
                for entry in focus:
                    lines.append(
                        "║     - "
                        f"{entry['pulse']} ({entry['status']}, priority={entry['priority']}) → "
                        f"{entry['recommendation']}"
                    )

        if self.memory_entries:
            lines.append("║ Recent Memory Sessions:")
            for entry in self.memory_entries:
                lines.append(
                    "║   ◦ "
                    f"{entry['timestamp']} — cycle {entry.get('cycle', 'n/a')} — "
                    f"commands={entry.get('commands', 0)} validations={entry.get('validations', 0)}"
                )

        if self.anchor_directory or self.anchor_opreturn:
            lines.append("║ Bridge Anchor Context:")
            if self.anchor_directory:
                lines.append(f"║   last batch → {self.anchor_directory}")
            if self.anchor_opreturn:
                lines.append(f"║   OP_RETURN → {self.anchor_opreturn}")
            if self.anchor_calldata:
                snippet = self.anchor_calldata.strip().replace("\n", " ")
                lines.append("║   ETH calldata → " + snippet[:120] + ("…" if len(snippet) > 120 else ""))

        if self.state.narrative:
            lines.append("║ Narrative excerpt:")
            lines.extend(textwrap.indent(self.state.narrative.strip(), "║   ").splitlines())

        lines.append("╚════════════════════════════════════════════════════╝")
        return "\n".join(lines)


class EchoNexusPortal(cmd.Cmd):
    """Interactive shell that connects Echo subsystems together."""

    intro = (
        "🔥 Echo Nexus Portal activated.  Type 'help' to discover commands, "
        "'cycle' to run an evolver loop, or 'status' for a full snapshot."
    )
    prompt = "Echo∇> "

    def __init__(
        self,
        *,
        network_enabled: bool = False,
        persist_artifact: bool = True,
        memory_store: Optional[JsonMemoryStore] = None,
    ) -> None:
        super().__init__()
        self.network_enabled = network_enabled
        self.persist_artifact = persist_artifact
        self.memory_store = memory_store or JsonMemoryStore()
        self.evolver = EchoEvolver(memory_store=self.memory_store)
        self.pulse_engine = EchoPulseEngine()
        self.bridge = BridgeEmitter()
        self._last_state: Optional[EvolverState] = None

        self._cycle_parser = argparse.ArgumentParser(prog="cycle", add_help=False)
        self._cycle_parser.add_argument("--network", dest="network", action="store_true")
        self._cycle_parser.add_argument("--no-network", dest="network", action="store_false")
        self._cycle_parser.add_argument("--persist", dest="persist", action="store_true")
        self._cycle_parser.add_argument("--no-persist", dest="persist", action="store_false")
        self._cycle_parser.set_defaults(network=self.network_enabled, persist=self.persist_artifact)

    # ------------------------------------------------------------------
    # Cycle control
    # ------------------------------------------------------------------
    def run_cycle(self, *, network: Optional[bool] = None, persist: Optional[bool] = None) -> EvolverState:
        """Execute a full EchoEvolver cycle and record it as a pulse."""

        state = self.evolver.run(
            enable_network=self.network_enabled if network is None else network,
            persist_artifact=self.persist_artifact if persist is None else persist,
        )
        self._last_state = state
        self._record_cycle_pulse(state)
        return state

    def do_cycle(self, arg: str) -> None:
        """Run a full EchoEvolver cycle.  Use --network/--no-network and --persist/--no-persist to override defaults."""

        try:
            namespace = self._cycle_parser.parse_args(shlex.split(arg))
        except SystemExit:
            print("Usage: cycle [--network|--no-network] [--persist|--no-persist]")
            return

        self.run_cycle(network=namespace.network, persist=namespace.persist)
        print(self.build_snapshot().render())

    # ------------------------------------------------------------------
    # Status + summaries
    # ------------------------------------------------------------------
    def build_snapshot(self, *, memory_limit: int = 3) -> PortalSnapshot:
        state = self._last_state or self.evolver.state
        pulses = self.pulse_engine.pulses(include_archived=False)
        advancement = self.pulse_engine.universal_advancement(include_archived=True)

        entries = []
        for context in self.memory_store.recent_executions(limit=memory_limit):
            entries.append(
                {
                    "timestamp": context.timestamp,
                    "cycle": context.cycle,
                    "summary": context.summary,
                    "commands": len(context.commands),
                    "validations": len(context.validations),
                }
            )

        anchor_dir = self.bridge.last_anchor_dir()
        snapshot = PortalSnapshot(
            state=state,
            pulses=pulses,
            advancement=advancement,
            memory_entries=entries,
            anchor_directory=str(anchor_dir) if anchor_dir else None,
            anchor_opreturn=self.bridge.last_opreturn(),
            anchor_calldata=self.bridge.last_eth_calldata(),
        )
        return snapshot

    def do_status(self, arg: str) -> None:  # noqa: D401 - user facing summary
        """Display the aggregated status of the Echo Nexus."""

        _ = arg  # The command ignores additional arguments.
        print(self.build_snapshot().render())

    # ------------------------------------------------------------------
    # Pulse management
    # ------------------------------------------------------------------
    def do_pulse(self, arg: str) -> None:
        """Manage pulses: pulse list|create|update|timeline|roadmap|cascade|archive|crystallize."""

        args = shlex.split(arg)
        if not args:
            print(self.do_pulse.__doc__)
            return

        command, *rest = args
        handler = getattr(self, f"_pulse_{command}", None)
        if handler is None:
            print(f"Unknown pulse command {command!r}. Available: list, create, update, timeline, roadmap, cascade, archive, crystallize")
            return

        handler(rest)

    def _pulse_list(self, _: Sequence[str]) -> None:
        pulses = self.pulse_engine.pulses(include_archived=True)
        if not pulses:
            print("No pulses registered yet.")
            return
        for pulse in pulses:
            print(
                f"- {pulse.name}: status={pulse.status} priority={pulse.priority} "
                f"created={pulse.created_at.isoformat()} updated={pulse.updated_at.isoformat()}"
            )

    def _pulse_create(self, args: Sequence[str]) -> None:
        parser = argparse.ArgumentParser(prog="pulse create", add_help=False)
        parser.add_argument("name")
        parser.add_argument("--resonance", default="Echo")
        parser.add_argument("--priority", default="medium")
        parser.add_argument("--data", nargs="*", default=[])
        try:
            ns = parser.parse_args(args)
        except SystemExit:
            print("Usage: pulse create <name> [--resonance R] [--priority P] [--data key=value ...]")
            return

        data = {}
        try:
            data = _parse_key_values(ns.data)
        except ValueError as exc:
            print(
                "error: "
                f"{exc}\nusage: pulse create <name> [--resonance R] [--priority P] [--data key=value ...]"
            )
            return

        try:
            pulse = self.pulse_engine.create_pulse(
                ns.name,
                resonance=ns.resonance,
                priority=ns.priority,
                data=data,
            )
        except ValueError as exc:
            print(f"error: {exc}")
            return
        print(f"Created pulse {pulse.name!r} with priority {pulse.priority}.")

    def _pulse_update(self, args: Sequence[str]) -> None:
        parser = argparse.ArgumentParser(prog="pulse update", add_help=False)
        parser.add_argument("name")
        parser.add_argument("--status")
        parser.add_argument("--resonance")
        parser.add_argument("--priority")
        parser.add_argument("--note")
        parser.add_argument("--data", nargs="*", default=[])
        try:
            ns = parser.parse_args(args)
        except SystemExit:
            print("Usage: pulse update <name> [--status S] [--resonance R] [--priority P] [--note TEXT] [--data key=value ...]")
            return

        data = {}
        if ns.data:
            try:
                data = _parse_key_values(ns.data)
            except ValueError as exc:
                print(
                    "error: "
                    f"{exc}\nusage: pulse update <name> [...] [--data key=value ...]"
                )
                return

        try:
            pulse = self.pulse_engine.update_pulse(
                ns.name,
                status=ns.status,
                resonance=ns.resonance,
                priority=ns.priority,
                data=data if data else None,
                note=ns.note,
            )
        except KeyError:
            print(f"pulse {ns.name!r} not found")
            return
        print(f"Updated pulse {pulse.name!r} → status={pulse.status} priority={pulse.priority}")

    def _pulse_timeline(self, args: Sequence[str]) -> None:
        if not args:
            print("Usage: pulse timeline <name>")
            return
        name = args[0]
        try:
            events = self.pulse_engine.history_for(name)
        except KeyError:
            print(f"pulse {name!r} not found")
            return
        if not events:
            print(f"pulse {name!r} has no timeline events yet")
            return
        for event in events:
            print(f"[{event.timestamp.isoformat()}] {event.status}: {event.message}")

    def _pulse_roadmap(self, _: Sequence[str]) -> None:
        roadmap = self.pulse_engine.universal_advancement(include_archived=True)
        print(json.dumps(roadmap, indent=2, ensure_ascii=False))

    def _pulse_cascade(self, args: Sequence[str]) -> None:
        parser = argparse.ArgumentParser(prog="pulse cascade", add_help=False)
        parser.add_argument("--status", action="append", dest="statuses")
        try:
            ns = parser.parse_args(args)
        except SystemExit:
            print("Usage: pulse cascade [--status STATUS] [--status STATUS]")
            return
        lines = self.pulse_engine.cascade(statuses=ns.statuses, include_archived=True)
        if not lines:
            print("No cascade entries match the requested filters.")
            return
        for line in lines:
            print(line)

    def _pulse_archive(self, args: Sequence[str]) -> None:
        parser = argparse.ArgumentParser(prog="pulse archive", add_help=False)
        parser.add_argument("name")
        parser.add_argument("--reason")
        try:
            ns = parser.parse_args(args)
        except SystemExit:
            print("Usage: pulse archive <name> [--reason TEXT]")
            return
        try:
            pulse = self.pulse_engine.archive(ns.name, reason=ns.reason)
        except KeyError:
            print(f"pulse {ns.name!r} not found")
            return
        print(f"Archived pulse {pulse.name!r}.")

    def _pulse_crystallize(self, args: Sequence[str]) -> None:
        if not args:
            print("Usage: pulse crystallize <name>")
            return
        name = args[0]
        try:
            pulse = self.pulse_engine.crystallize(name)
        except KeyError:
            print(f"pulse {name!r} not found")
            return
        print(f"Crystallized pulse {pulse.name!r}.")

    # ------------------------------------------------------------------
    # Bridge helpers
    # ------------------------------------------------------------------
    def do_bridge(self, arg: str) -> None:
        """Show bridge anchoring context or attempt a single process cycle."""

        args = shlex.split(arg)
        if args and args[0] == "process":
            batch_size = None
            if len(args) > 1:
                try:
                    batch_size = int(args[1])
                except ValueError:
                    print("Batch size must be an integer")
                    return
            out = self.bridge.process_once(batch_size=batch_size)
            if out is None:
                print("No pending bridge items to anchor.")
            else:
                print(f"Anchored bridge batch at {out}")
        else:
            snapshot = self.build_snapshot()
            if not (snapshot.anchor_directory or snapshot.anchor_opreturn):
                print("No bridge anchors have been generated yet.")
            else:
                print(snapshot.render())

    # ------------------------------------------------------------------
    # Memory inspection
    # ------------------------------------------------------------------
    def do_memory(self, arg: str) -> None:
        """Show recent memory sessions with optional limit override."""

        args = shlex.split(arg)
        limit = 5
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                print("Memory limit must be an integer")
                return

        sessions = self.memory_store.recent_executions(limit=limit)
        if not sessions:
            print("Memory store has no recorded executions yet.")
            return
        for context in sessions:
            print(
                f"- {context.timestamp} cycle={context.cycle} commands={len(context.commands)} "
                f"validations={len(context.validations)} summary={(context.summary or '').strip()[:80]}"
            )

    # ------------------------------------------------------------------
    # Quality-of-life hooks
    # ------------------------------------------------------------------
    def do_quit(self, arg: str) -> bool:  # noqa: D401 - command exit pattern
        """Exit the portal."""

        _ = arg
        print("Echo Nexus Portal closing. 🜂")
        return True

    do_exit = do_quit

    def do_EOF(self, arg: str) -> bool:  # noqa: N802 - cmd.Cmd API
        return self.do_quit(arg)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _record_cycle_pulse(self, state: EvolverState) -> None:
        """Create or refresh the pulse representing the latest cycle."""

        pulse_name = f"cycle-{state.cycle}"
        summary = (
            f"cycle {state.cycle} joy={state.emotional_drive.joy:.2f} nodes={state.system_metrics.network_nodes} "
            f"key={'yes' if state.vault_key else 'no'}"
        )
        data = {
            "glyphs": state.glyphs,
            "mythocode": state.mythocode,
            "events": state.network_cache.get("propagation_events", []),
            "quantum_key": state.vault_key,
        }
        try:
            self.pulse_engine.create_pulse(
                pulse_name,
                resonance="cycle",
                priority="high",
                data=data,
            )
        except ValueError:
            self.pulse_engine.update_pulse(
                pulse_name,
                data=data,
                note=summary,
            )
        else:
            self.pulse_engine.update_pulse(
                pulse_name,
                status="crystallized",
                data=data,
                note=summary,
            )


def launch_portal(
    *,
    network_enabled: bool = False,
    persist_artifact: bool = True,
    auto_cycles: int = 0,
    snapshot: bool = False,
) -> EchoNexusPortal:
    """Helper used by the module CLI and external callers."""

    portal = EchoNexusPortal(
        network_enabled=network_enabled,
        persist_artifact=persist_artifact,
    )

    for _ in range(max(0, auto_cycles)):
        portal.run_cycle()

    if snapshot:
        print(portal.build_snapshot().render())

    return portal


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command line entry point for the Echo Nexus Portal."""

    parser = argparse.ArgumentParser(description="Echo Nexus interactive portal")
    parser.add_argument("--network", action="store_true", help="Enable live network propagation during cycles")
    parser.add_argument("--no-artifact", dest="persist_artifact", action="store_false", help="Skip writing evolution artifacts")
    parser.add_argument("--auto-cycles", type=int, default=0, help="Run the specified number of cycles before starting the shell")
    parser.add_argument("--snapshot", action="store_true", help="Print a snapshot after auto cycles and exit")
    parser.set_defaults(persist_artifact=True)

    args = parser.parse_args(list(argv) if argv is not None else None)

    portal = launch_portal(
        network_enabled=args.network,
        persist_artifact=args.persist_artifact,
        auto_cycles=args.auto_cycles,
        snapshot=args.snapshot,
    )

    if args.snapshot:
        return 0

    try:
        portal.cmdloop()
    except KeyboardInterrupt:
        print("\nEcho Nexus Portal interrupted. 🜂")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI behaviour
    raise SystemExit(main())
