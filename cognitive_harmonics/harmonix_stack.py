"""Cognitive Harmonix rendition of the Echo Mesh / Orchestrator stack.

The original design brief described a C++23 mini-stack composed of SWIM-lite
gossip discovery, a policy virtual machine, Noise-style handshakes, telemetry,
and a CLI orchestrator.  This module translates those concerns into the
``cognitive_harmonics`` universe so the resulting payloads can be consumed by
tools that expect the Harmonix schema rather than raw network side-effects.

The implementation deliberately avoids opening sockets or spawning subprocesses
so it can be exercised in unit tests and scripted environments.  Each component
simulates the behaviour of its systems counterpart while recording rich
metadata that feeds directly into the Harmonix payload produced by
``HarmonixOrchestrator.run_cycle``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import blake2b
from typing import Dict, Iterable, List, Tuple
import json


# ---------------------------------------------------------------------------
# Core utilities – NetAddr, SpinLock, and a light ring buffer.
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class NetAddr:
    """Lightweight host:port representation used by the mesh simulation."""

    ip: str
    port: int

    @property
    def label(self) -> str:
        return f"{self.ip}:{self.port}"


class SpinLock:
    """Minimal spin lock abstraction wrapping an optimistic state flag."""

    __slots__ = ("_locked",)

    def __init__(self) -> None:
        self._locked = False

    def acquire(self) -> None:
        if self._locked:
            raise RuntimeError("SpinLock already acquired in this cooperative model")
        self._locked = True

    def release(self) -> None:
        if not self._locked:
            raise RuntimeError("SpinLock not acquired")
        self._locked = False

    def __enter__(self) -> "SpinLock":
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


class RingBuffer:
    """Simple ring buffer used to emulate the bridge telemetry counters."""

    __slots__ = ("_buffer", "_read", "_write")

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._buffer: List[int] = [0] * capacity
        self._read = 0
        self._write = 0

    def _advance(self, idx: int, delta: int) -> int:
        return (idx + delta) % len(self._buffer)

    def write(self, value: int) -> None:
        self._buffer[self._write] = value
        self._write = self._advance(self._write, 1)
        if self._write == self._read:
            self._read = self._advance(self._read, 1)

    def read_all(self) -> List[int]:
        idx = self._read
        out: List[int] = []
        while idx != self._write:
            out.append(self._buffer[idx])
            idx = self._advance(idx, 1)
        return out


# ---------------------------------------------------------------------------
# Mesh simulation – SWIM-lite inspired membership table.
# ---------------------------------------------------------------------------


class SwimState(Enum):
    ALIVE = "alive"
    SUSPECT = "suspect"
    DEAD = "dead"


@dataclass(slots=True)
class SwimMember:
    addr: NetAddr
    incarnation: int
    state: SwimState
    heartbeat: float


class SwimLite:
    """Self-contained SWIM-lite mesh simulation for deterministic cycles."""

    def __init__(self, bind: NetAddr, seeds: Iterable[NetAddr]) -> None:
        self.bind = bind
        self.members: Dict[str, SwimMember] = {
            bind.label: SwimMember(bind, incarnation=0, state=SwimState.ALIVE, heartbeat=0.0)
        }
        for seed in seeds:
            self.members[seed.label] = SwimMember(
                seed, incarnation=0, state=SwimState.SUSPECT, heartbeat=0.0
            )
        self.events: List[str] = ["Mesh initialised"]

    def step(self, cycle: int) -> List[SwimMember]:
        for idx, member in enumerate(self.members.values()):
            seed = f"{member.addr.label}|{cycle}|{idx}".encode("utf-8")
            digest = blake2b(seed, digest_size=1).digest()[0]
            if digest % 11 == 0:
                member.state = SwimState.DEAD
            elif digest % 5 == 0:
                member.state = SwimState.SUSPECT
            else:
                member.state = SwimState.ALIVE
            member.incarnation = cycle
            member.heartbeat = cycle * 1.5 + idx
        self.events.append(f"Mesh step completed for cycle {cycle}")
        return list(self.members.values())

    def snapshot(self) -> List[SwimMember]:
        return [
            SwimMember(m.addr, m.incarnation, m.state, m.heartbeat)
            for m in self.members.values()
        ]


# ---------------------------------------------------------------------------
# Noise-XX inspired handshake (deterministic stand-in).
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class NoiseKeys:
    rx: bytes
    tx: bytes


class NoiseXX:
    """Minimal Noise-XX handshake using deterministic blake2b derivations."""

    def __init__(self, label: str = "harmonix") -> None:
        self.label = label
        self._stage = 0
        self._seed = blake2b(label.encode("utf-8"), digest_size=32).digest()
        self._their_ephemeral: bytes | None = None
        self._their_static: bytes | None = None
        self._keys: NoiseKeys | None = None

    def stage1(self) -> bytes:
        if self._stage != 0:
            raise RuntimeError("stage1 already performed")
        self._stage = 1
        return blake2b(self._seed + b"|stage1", digest_size=32).digest()

    def stage2(self, msg1: bytes) -> bytes:
        if self._stage != 1:
            raise RuntimeError("stage2 called out of order")
        transcript = msg1 + self._seed + b"|stage2"
        digest = blake2b(transcript, digest_size=64).digest()
        self._their_ephemeral = digest[:32]
        self._their_static = digest[32:]
        self._stage = 2
        return digest

    def stage3(self) -> bytes:
        if self._stage != 2:
            raise RuntimeError("stage3 called out of order")
        combined = (self._their_ephemeral or b"") + (self._their_static or b"")
        digest = blake2b(combined + self._seed + b"|stage3", digest_size=64).digest()
        self._keys = NoiseKeys(rx=digest[:32], tx=digest[32:])
        self._stage = 3
        return digest[:32]

    def complete(self) -> bool:
        return self._stage == 3 and self._keys is not None

    def keys(self) -> NoiseKeys:
        if not self.complete():
            raise RuntimeError("Handshake incomplete")
        return self._keys  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Policy VM – simple DSL evaluator with numeric, boolean, and string inputs.
# ---------------------------------------------------------------------------


class PolicyActionType(str, Enum):
    ROUTE = "route"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    DENY = "deny"
    QUARANTINE = "quarantine"
    NONE = "none"


@dataclass(slots=True)
class PolicyAction:
    type: PolicyActionType
    route_tag: str | None = None
    delta: int = 0
    seconds: int = 0


@dataclass(slots=True)
class PolicyInput:
    num: Dict[str, float] = field(default_factory=dict)
    flag: Dict[str, bool] = field(default_factory=dict)
    string: Dict[str, str] = field(default_factory=dict)


class PolicyVM:
    """Parse and execute the miniature policy DSL."""

    def __init__(self) -> None:
        self._program: List[Tuple[str, str, str, str, str]] = []

    def load_text(self, program: str) -> Tuple[bool, str | None]:
        import re

        self._program.clear()
        rule_re = re.compile(
            r"when\s+([a-zA-Z0-9_.]+)\s*(==|!=|<=|>=|<|>)\s*(.+?)\s*then\s*([a-z_]+)\s*(.*?);",
            re.DOTALL,
        )
        for match in rule_re.finditer(program):
            lhs, op, rhs, act, arg = match.groups()
            self._program.append((lhs.strip(), op.strip(), rhs.strip(), act.strip(), arg.strip()))
        if not self._program:
            return False, "no valid rules parsed"
        return True, None

    def eval(self, inputs: PolicyInput) -> List[PolicyAction]:
        actions: List[PolicyAction] = []
        for lhs, op, rhs, act, arg in self._program:
            if lhs in inputs.num:
                lhs_value = inputs.num[lhs]
                rhs_value = float(rhs)
                if not self._compare(lhs_value, rhs_value, op):
                    continue
            elif lhs in inputs.flag:
                lhs_value = inputs.flag[lhs]
                rhs_bool = rhs.lower() in {"true", "1"}
                if not self._compare(lhs_value, rhs_bool, op):
                    continue
            elif lhs in inputs.string:
                lhs_value = inputs.string[lhs]
                rhs_str = rhs.strip("\"")
                if not self._compare(lhs_value, rhs_str, op):
                    continue
            else:
                continue

            actions.append(self._build_action(act, arg))
        return actions

    @staticmethod
    def _compare(lhs: float | bool | str, rhs: float | bool | str, op: str) -> bool:
        if op == "==":
            return lhs == rhs
        if op == "!=":
            return lhs != rhs
        if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
            if op == "<":
                return lhs < rhs
            if op == ">":
                return lhs > rhs
            if op == "<=":
                return lhs <= rhs
            if op == ">=":
                return lhs >= rhs
        return False

    @staticmethod
    def _build_action(action: str, raw_arg: str) -> PolicyAction:
        cleaned = raw_arg.strip()
        if action == PolicyActionType.ROUTE:
            return PolicyAction(PolicyActionType.ROUTE, route_tag=cleaned.strip('"'))
        if action == PolicyActionType.SCALE_OUT:
            return PolicyAction(PolicyActionType.SCALE_OUT, delta=int(cleaned.replace("+", "")))
        if action == PolicyActionType.SCALE_IN:
            return PolicyAction(PolicyActionType.SCALE_IN, delta=int(cleaned.replace("+", "")))
        if action == PolicyActionType.DENY:
            return PolicyAction(PolicyActionType.DENY)
        if action == PolicyActionType.QUARANTINE:
            return PolicyAction(PolicyActionType.QUARANTINE, seconds=int(cleaned or "0"))
        return PolicyAction(PolicyActionType.NONE)


# ---------------------------------------------------------------------------
# Harmonix orchestrator – ties mesh, policy, handshake, and telemetry together.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BridgeRoute:
    tag: str
    target_hp: str
    min_pairs: int
    active_pairs: int = 0


@dataclass(slots=True)
class Telemetry:
    bytes_up: int = 0
    bytes_down: int = 0
    drops: int = 0
    pairs: int = 0


@dataclass(slots=True)
class HarmonixOrchestratorState:
    cycle: int = 0
    telemetry: Telemetry = field(default_factory=Telemetry)
    routes: Dict[str, BridgeRoute] = field(default_factory=dict)
    actions: List[PolicyAction] = field(default_factory=list)
    events: List[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        self.events.append(message)

    @property
    def active_pairs(self) -> int:
        return sum(route.active_pairs for route in self.routes.values())


class HarmonixOrchestrator:
    """Deterministic orchestrator translating stack state into Harmonix payloads."""

    def __init__(
        self,
        mesh_bind: NetAddr,
        seeds: Iterable[NetAddr],
        policy_text: str,
    ) -> None:
        self.mesh = SwimLite(mesh_bind, seeds)
        self.policy = PolicyVM()
        ok, err = self.policy.load_text(policy_text)
        if not ok:
            raise ValueError(err or "policy parsing failed")
        self.handshake = NoiseXX(mesh_bind.label)
        self.state = HarmonixOrchestratorState()
        self.ring = RingBuffer(16)
        self.state.record("Harmonix orchestrator initialised")

    # ------------------------------------------------------------------
    # Declarative route helpers
    # ------------------------------------------------------------------

    def ensure_route(self, tag: str, target_hp: str, min_pairs: int) -> None:
        self.state.routes[tag] = BridgeRoute(tag, target_hp, min_pairs)
        self.state.record(f"Route ensured for {tag} -> {target_hp} (min {min_pairs})")

    # ------------------------------------------------------------------
    # Core cycle logic
    # ------------------------------------------------------------------

    def _apply_actions(self, actions: List[PolicyAction]) -> None:
        self.state.actions = actions
        for action in actions:
            if action.type == PolicyActionType.SCALE_OUT:
                self._scale_out(action.delta)
            elif action.type == PolicyActionType.SCALE_IN:
                self._scale_in(action.delta)
            elif action.type == PolicyActionType.ROUTE and action.route_tag:
                self.state.record(f"Route preference signalled for {action.route_tag}")
            elif action.type == PolicyActionType.DENY:
                self.state.record("Deny action triggered (no-op in simulation)")
            elif action.type == PolicyActionType.QUARANTINE:
                self.state.record(
                    f"Quarantine enforced for {action.seconds} seconds (simulated)"
                )

    def _scale_out(self, count: int) -> None:
        if not self.state.routes:
            return
        for idx in range(count):
            route = list(self.state.routes.values())[idx % len(self.state.routes)]
            route.active_pairs += 1
            self.state.record(f"Spawned simulated pair on {route.tag}")

    def _scale_in(self, count: int) -> None:
        for _ in range(count):
            # remove from the most populated route first
            if not self.state.routes:
                break
            route = max(self.state.routes.values(), key=lambda r: r.active_pairs)
            if route.active_pairs == 0:
                break
            route.active_pairs -= 1
            self.state.record(f"Removed simulated pair from {route.tag}")

    def _enforce_minimums(self) -> None:
        for route in self.state.routes.values():
            if route.active_pairs < route.min_pairs:
                delta = route.min_pairs - route.active_pairs
                route.active_pairs += delta
                self.state.record(
                    f"Raised {route.tag} to minimum pairs (added {delta})"
                )

    def _update_telemetry(self, cycle: int) -> None:
        telemetry = self.state.telemetry
        telemetry.pairs = self.state.active_pairs
        base = cycle * 4096 + telemetry.pairs * 32768
        telemetry.bytes_up = base + 2048
        telemetry.bytes_down = base - 1024 if base > 1024 else base
        telemetry.drops = cycle % 7
        self.ring.write(telemetry.bytes_up)
        self.state.record(
            f"Telemetry updated – pairs={telemetry.pairs} bytes_up={telemetry.bytes_up}"
        )

    def _handshake_cycle(self) -> NoiseKeys:
        msg1 = self.handshake.stage1()
        msg2 = self.handshake.stage2(msg1)
        self.state.record(f"Handshake stage2 digest {msg2.hex()[:16]}")
        self.handshake.stage3()
        keys = self.handshake.keys()
        self.state.record("Noise handshake completed")
        return keys

    def run_cycle(self) -> Tuple[HarmonixOrchestratorState, Dict[str, object]]:
        self.state.cycle += 1
        cycle = self.state.cycle
        self.state.record(f"Cycle advanced to {cycle}")

        members = self.mesh.step(cycle)
        member_dead = any(member.state is SwimState.DEAD for member in members)
        policy_input = PolicyInput(
            num={
                "pairs": float(self.state.active_pairs),
                "rtt_ms": 10.0 + cycle * 1.5,
                "loss_pct": 0.5 + cycle * 0.1,
            },
            flag={"member.dead": member_dead},
        )
        actions = self.policy.eval(policy_input)
        self._apply_actions(actions)
        self._enforce_minimums()
        self._update_telemetry(cycle)
        keys = self._handshake_cycle()

        payload = self._build_payload(members, keys)
        return self.state, payload

    # ------------------------------------------------------------------
    # Payload composition
    # ------------------------------------------------------------------

    def _build_payload(self, members: List[SwimMember], keys: NoiseKeys) -> Dict[str, object]:
        metadata = {
            "cycle": self.state.cycle,
            "mesh_members": [
                {
                    "addr": member.addr.label,
                    "incarnation": member.incarnation,
                    "state": member.state.value,
                    "heartbeat": member.heartbeat,
                }
                for member in members
            ],
            "routes": {
                tag: {
                    "target": route.target_hp,
                    "min_pairs": route.min_pairs,
                    "active_pairs": route.active_pairs,
                }
                for tag, route in self.state.routes.items()
            },
            "telemetry": {
                "bytes_up": self.state.telemetry.bytes_up,
                "bytes_down": self.state.telemetry.bytes_down,
                "drops": self.state.telemetry.drops,
                "pairs": self.state.telemetry.pairs,
                "ring_history": self.ring.read_all(),
            },
            "handshake": {
                "rx": keys.rx.hex(),
                "tx": keys.tx.hex(),
            },
            "actions": [
                {
                    "type": action.type.value,
                    "route_tag": action.route_tag,
                    "delta": action.delta,
                    "seconds": action.seconds,
                }
                for action in self.state.actions
            ],
            "events": list(self.state.events),
            "mesh_events": list(self.mesh.events),
        }
        return {
            "waveform": "complex_harmonic",
            "resonance_factor": round(0.8 + 0.04 * self.state.cycle, 6),
            "compression": True,
            "symbolic_inflection": "fractal",
            "lyricism_mode": True,
            "emotional_tuning": "energizing",
            "metadata": metadata,
        }


# ---------------------------------------------------------------------------
# CLI helper – mirrors the structure used by other Harmonix modules.
# ---------------------------------------------------------------------------


def main() -> None:
    orchestrator = HarmonixOrchestrator(
        mesh_bind=NetAddr("127.0.0.1", 7946),
        seeds=[NetAddr("127.0.0.1", 7947)],
        policy_text="when pairs < 4 then scale_out +2; when rtt_ms > 25 then route \"alt\";",
    )
    orchestrator.ensure_route("primary", "10.0.0.5:9000", min_pairs=2)
    _, payload = orchestrator.run_cycle()
    print(json.dumps(payload, indent=2, ensure_ascii=False))


__all__ = [
    "BridgeRoute",
    "HarmonixOrchestrator",
    "HarmonixOrchestratorState",
    "NetAddr",
    "NoiseKeys",
    "NoiseXX",
    "PolicyAction",
    "PolicyActionType",
    "PolicyInput",
    "PolicyVM",
    "RingBuffer",
    "SpinLock",
    "SwimLite",
    "SwimMember",
    "SwimState",
    "Telemetry",
    "main",
]
