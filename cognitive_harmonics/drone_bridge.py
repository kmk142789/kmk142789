"""Cognitive Harmonix ⇄ Drone Bridge control core.

This module contains a compact but production-ready control core for a small
multisensor drone.  It fuses incoming frames into a harmonised state, evaluates
safety policies, plans the next action, and relays commands to actuators.

The default implementation wires together a fully asynchronous event bus with
mock sensors and actuators so the system can be exercised in simulation mode.
Hardware-specific adapters can be registered without modifying the core logic.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses as dc
import json
import math
import os
import random
import signal
import time
from collections import deque
from pathlib import Path
from typing import Any, Awaitable, Callable, Deque, Dict, List, Optional, Tuple

###############################################################################
# Telemetry utilities
###############################################################################

LOG_DIR = Path(os.environ.get("CHX_LOG_DIR", "./logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JsonlLogger:
    """Very small helper that emits newline-delimited JSON telemetry."""

    def __init__(self, path: Path):
        self.path = path
        self._handle = path.open("a", encoding="utf-8")

    def write(self, event: str, **payload: Any) -> None:
        record = {"ts": time.time(), "event": event, **payload}
        self._handle.write(json.dumps(record) + "\n")
        self._handle.flush()

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._handle.close()


LOGGER = JsonlLogger(LOG_DIR / f"chx_{int(time.time())}.jsonl")

###############################################################################
# Event bus
###############################################################################

EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class EventBus:
    """Async publish/subscribe fabric that decouples each subsystem."""

    def __init__(self) -> None:
        self._subs: Dict[str, List[EventHandler]] = {}

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._subs.setdefault(topic, []).append(handler)

    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        handlers = list(self._subs.get(topic, ()))
        if not handlers:
            return
        await asyncio.gather(*(handler(payload) for handler in handlers))


BUS = EventBus()

###############################################################################
# Sensor frames and harmonised state
###############################################################################


@dc.dataclass(slots=True)
class Frame:
    ts: float
    source: str
    data: Dict[str, Any]
    confidence: float = 1.0


@dc.dataclass
class HarmonicState:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    obstacles: List[Tuple[float, float, float]] = dc.field(default_factory=list)
    wind: float = 0.0
    battery: float = 1.0
    gps_fix: bool = False
    gps_hdop: float = 99.0
    pose_conf: float = 0.2
    env_conf: float = 0.2
    power_conf: float = 0.2

    def as_dict(self) -> Dict[str, Any]:
        return dc.asdict(self)


class Harmonizer:
    """Fuse incoming frames into a single harmonic state."""

    def __init__(self) -> None:
        self.state = HarmonicState()
        self.history: Deque[Frame] = deque(maxlen=64)
        BUS.subscribe("frame", self.on_frame)

    async def on_frame(self, payload: Dict[str, Any]) -> None:
        frame: Frame = payload["frame"]
        self.history.append(frame)
        state = self.state

        if frame.source == "imu":
            ax, ay, az = frame.data.get("accel", (0.0, 0.0, 0.0))
            gx, gy, gz = frame.data.get("gyro", (0.0, 0.0, 0.0))
            del gx, gy  # currently unused
            dt = 0.02
            state.vx += ax * dt
            state.vy += ay * dt
            state.vz += az * dt
            state.yaw += gz * dt
            state.pose_conf = min(1.0, 0.6 * frame.confidence + 0.4 * state.pose_conf)
        elif frame.source == "gps":
            state.x = frame.data.get("x", state.x)
            state.y = frame.data.get("y", state.y)
            state.z = frame.data.get("z", state.z)
            state.gps_fix = frame.data.get("fix", state.gps_fix)
            state.gps_hdop = frame.data.get("hdop", state.gps_hdop)
            state.pose_conf = min(1.0, 0.7 * frame.confidence + 0.3 * state.pose_conf)
        elif frame.source == "vision":
            state.obstacles = frame.data.get("obstacles", [])
            state.env_conf = min(1.0, 0.7 * frame.confidence + 0.3 * state.env_conf)
        elif frame.source == "power":
            state.battery = frame.data.get("battery", state.battery)
            state.power_conf = min(1.0, 0.7 * frame.confidence + 0.3 * state.power_conf)
        elif frame.source == "wind":
            state.wind = frame.data.get("speed", state.wind)

        LOGGER.write("harmonizer_update", state=state.as_dict())


HARMONIZER = Harmonizer()

###############################################################################
# Policies / guardrails
###############################################################################


@dc.dataclass(slots=True)
class PolicyConfig:
    geofence_radius_m: float = 120.0
    max_alt_m: float = 60.0
    min_batt: float = 0.18
    max_wind_mps: float = 8.0


class Policy:
    def __init__(self, cfg: PolicyConfig) -> None:
        self.cfg = cfg

    def violations(self, state: HarmonicState) -> List[str]:
        errs: List[str] = []
        if math.hypot(state.x, state.y) > self.cfg.geofence_radius_m:
            errs.append("geofence")
        if state.z > self.cfg.max_alt_m:
            errs.append("altitude")
        if state.battery < self.cfg.min_batt:
            errs.append("battery")
        if state.wind > self.cfg.max_wind_mps:
            errs.append("wind")
        for dx, dy, dz in state.obstacles:
            if math.hypot(dx, dy) < 2.0 and abs(dz) < 3.0:
                errs.append("obstacle")
                break
        return errs


POLICY = Policy(PolicyConfig())

###############################################################################
# Planner
###############################################################################


@dc.dataclass(slots=True)
class Goal:
    kind: str
    params: Dict[str, Any]


class Planner:
    def __init__(self) -> None:
        self.stack: List[Goal] = [Goal("hover", {"x": 0.0, "y": 0.0, "z": 2.0})]
        BUS.subscribe("tick", self.on_tick)

    async def on_tick(self, payload: Dict[str, Any]) -> None:  # noqa: ARG002
        state = HARMONIZER.state
        violations = POLICY.violations(state)
        if violations:
            cmd = self.emergency(state, violations)
        else:
            cmd = self.plan_step(state)
        await BUS.publish("cmd", cmd)
        LOGGER.write("plan", cmd=cmd, violations=violations, state=state.as_dict())

    def plan_step(self, state: HarmonicState) -> Dict[str, Any]:
        if not self.stack:
            self.stack.append(Goal("hover", {"x": state.x, "y": state.y, "z": max(1.0, state.z)}))
        goal = self.stack[-1]
        if goal.kind in {"hover", "goto"}:
            return self._cmd_towards(goal.params["x"], goal.params["y"], goal.params["z"], state)
        if goal.kind == "land":
            return {"op": "land"}
        if goal.kind == "survey":
            waypoints: List[Tuple[float, float, float]] = goal.params.setdefault(
                "waypoints",
                [(0.0, 0.0, 3.0), (10.0, 0.0, 3.0), (10.0, 10.0, 3.0), (0.0, 10.0, 3.0)],
            )
            idx = goal.params.setdefault("idx", 0)
            tx, ty, tz = waypoints[idx]
            cmd = self._cmd_towards(tx, ty, tz, state)
            if math.hypot(state.x - tx, state.y - ty) < 1.0 and abs(state.z - tz) < 0.7:
                goal.params["idx"] = (idx + 1) % len(waypoints)
            return cmd
        return {"op": "hold"}

    def emergency(self, state: HarmonicState, violations: List[str]) -> Dict[str, Any]:
        if "battery" in violations:
            return {"op": "rtl"}
        if "geofence" in violations:
            ang = math.atan2(state.y, state.x)
            return {
                "op": "vel",
                "vx": -2.0 * math.cos(ang),
                "vy": -2.0 * math.sin(ang),
                "vz": 0.0,
                "yaw": 0.0,
            }
        if "wind" in violations:
            return {"op": "hold"}
        if "altitude" in violations:
            return {"op": "vel", "vx": 0.0, "vy": 0.0, "vz": -0.8, "yaw": 0.0}
        if "obstacle" in violations:
            return {"op": "vel", "vx": -0.8, "vy": 0.0, "vz": 0.2, "yaw": 0.0}
        return {"op": "hold"}

    @staticmethod
    def _cmd_towards(tx: float, ty: float, tz: float, state: HarmonicState) -> Dict[str, Any]:
        kxy, kz = 0.3, 0.45
        vx = max(-1.5, min(1.5, (tx - state.x) * kxy))
        vy = max(-1.5, min(1.5, (ty - state.y) * kxy))
        vz = max(-1.0, min(1.0, (tz - state.z) * kz))
        return {"op": "vel", "vx": vx, "vy": vy, "vz": vz, "yaw": 0.0}


PLANNER = Planner()

###############################################################################
# Actuators
###############################################################################


class ActuatorAdapter:
    async def send(self, cmd: Dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class MockActuator(ActuatorAdapter):
    async def send(self, cmd: Dict[str, Any]) -> None:
        LOGGER.write("actuator_cmd", **cmd)


ACTUATOR: ActuatorAdapter = MockActuator()


async def _cmd_sink(payload: Dict[str, Any]) -> None:
    await ACTUATOR.send(payload)


BUS.subscribe("cmd", _cmd_sink)

###############################################################################
# Sensors
###############################################################################


class Sensor:
    def __init__(self, name: str, fps: float) -> None:
        self.name = name
        self.dt = 1.0 / max(1.0, fps)
        self._task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            frame = await self.read()
            await BUS.publish("frame", {"frame": frame})
            await asyncio.sleep(self.dt)

    async def read(self) -> Frame:  # pragma: no cover - interface
        raise NotImplementedError


class MockIMU(Sensor):
    def __init__(self, fps: float = 50.0) -> None:
        super().__init__("imu", fps)

    async def read(self) -> Frame:
        ax, ay, az = (random.uniform(-0.1, 0.1) for _ in range(3))
        gz = random.uniform(-0.05, 0.05)
        return Frame(
            ts=time.time(),
            source="imu",
            data={"accel": (ax, ay, az), "gyro": (0.0, 0.0, gz)},
            confidence=0.8,
        )


class MockGPS(Sensor):
    def __init__(self, drift: float = 0.2) -> None:
        super().__init__("gps", fps=5.0)
        self.t = 0.0
        self.drift = drift

    async def read(self) -> Frame:
        self.t += self.dt
        x = 5.0 * math.sin(self.t / 5.0) + random.uniform(-self.drift, self.drift)
        y = 5.0 * math.cos(self.t / 5.0) + random.uniform(-self.drift, self.drift)
        z = 2.0 + 0.2 * math.sin(self.t / 3.0)
        return Frame(
            ts=time.time(),
            source="gps",
            data={"x": x, "y": y, "z": z, "fix": True, "hdop": 0.9},
            confidence=0.9,
        )


class MockVision(Sensor):
    def __init__(self, fps: float = 10.0) -> None:
        super().__init__("vision", fps)

    async def read(self) -> Frame:
        obstacles: List[Tuple[float, float, float]] = []
        if random.random() < 0.15:
            obstacles.append(
                (
                    random.uniform(0.5, 1.5),
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.5, 0.5),
                )
            )
        return Frame(
            ts=time.time(),
            source="vision",
            data={"obstacles": obstacles},
            confidence=0.7,
        )


class MockPower(Sensor):
    def __init__(self) -> None:
        super().__init__("power", fps=1.0)
        self.batt = 1.0

    async def read(self) -> Frame:
        self.batt = max(0.0, self.batt - 0.0008)
        return Frame(
            ts=time.time(),
            source="power",
            data={"battery": self.batt},
            confidence=0.95,
        )


class MockWind(Sensor):
    def __init__(self, fps: float = 0.5) -> None:
        super().__init__("wind", fps)

    async def read(self) -> Frame:
        return Frame(
            ts=time.time(),
            source="wind",
            data={"speed": random.uniform(0.0, 6.0)},
            confidence=0.6,
        )


###############################################################################
# Runtime orchestration
###############################################################################


class Runtime:
    def __init__(self) -> None:
        self.sensors: List[Sensor] = [
            MockIMU(fps=50.0),
            MockGPS(),
            MockVision(fps=10.0),
            MockPower(),
            MockWind(fps=0.5),
        ]
        BUS.subscribe("tick", self.on_tick)

    async def on_tick(self, payload: Dict[str, Any]) -> None:  # noqa: ARG002
        if int(time.time()) % 5 == 0:
            LOGGER.write("heartbeat", state=HARMONIZER.state.as_dict())

    async def start(self) -> None:
        for sensor in self.sensors:
            await sensor.start()
        asyncio.create_task(self._ticker())

    async def _ticker(self) -> None:
        while True:
            await BUS.publish("tick", {"t": time.time()})
            await asyncio.sleep(0.05)


###############################################################################
# Public goal control API
###############################################################################


def set_goal_hover(x: float, y: float, z: float) -> None:
    PLANNER.stack.append(Goal("hover", {"x": x, "y": y, "z": z}))
    LOGGER.write("api_set_goal", kind="hover", x=x, y=y, z=z)


def set_goal_goto(x: float, y: float, z: float) -> None:
    PLANNER.stack.append(Goal("goto", {"x": x, "y": y, "z": z}))
    LOGGER.write("api_set_goal", kind="goto", x=x, y=y, z=z)


def set_goal_survey(waypoints: List[Tuple[float, float, float]]) -> None:
    PLANNER.stack.append(Goal("survey", {"waypoints": waypoints}))
    LOGGER.write("api_set_goal", kind="survey", w=len(waypoints))


def set_goal_land() -> None:
    PLANNER.stack.append(Goal("land", {}))
    LOGGER.write("api_set_goal", kind="land")


###############################################################################
# Main entry point
###############################################################################


async def amain(run_duration: float | None = None) -> None:
    runtime = Runtime()
    await runtime.start()
    set_goal_survey([(0.0, 0.0, 3.0), (8.0, 0.0, 3.0), (8.0, 8.0, 3.0), (0.0, 8.0, 3.0)])

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _stop() -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)

    if run_duration is not None:
        loop.call_later(run_duration, stop_event.set)

    await stop_event.wait()


def main() -> None:
    try:
        asyncio.run(amain())
    finally:
        LOGGER.close()


if __name__ == "__main__":
    main()
