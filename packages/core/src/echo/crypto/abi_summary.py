"""Utilities for summarising Ethereum contract ABIs.

The Echo toolchain frequently needs to reason about on-chain contracts when
building provenance data or mirroring sidechain movements.  Rather than pulling
in a heavyweight web3 dependency, this module offers a tiny, well-typed summary
of ABI entries that can be used for reporting, indexing, or signature checks.

The goal is not to implement the entire Ethereum ABI specification; instead we
normalise the most common fields (functions, events, constructors) into simple
structures that are pleasant to inspect and test.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


@dataclass(frozen=True, slots=True)
class AbiParameter:
    """A single ABI parameter description."""

    name: str
    type: str
    indexed: bool = False

    def __post_init__(self) -> None:
        if not self.type:
            msg = "ABI parameter type cannot be empty"
            raise ValueError(msg)

    @property
    def canonical(self) -> str:
        """Return the canonical type string used in signature calculations."""

        return self.type


@dataclass(frozen=True, slots=True)
class FunctionEntry:
    """Normalised view of a function ABI entry."""

    name: str
    inputs: tuple[AbiParameter, ...]
    outputs: tuple[AbiParameter, ...]
    state_mutability: str
    payable: bool
    constant: bool

    def __post_init__(self) -> None:
        if not self.name:
            msg = "Function ABI entries must include a name"
            raise ValueError(msg)

    @property
    def signature(self) -> str:
        """Return the canonical function signature string."""

        params = ",".join(param.canonical for param in self.inputs)
        return f"{self.name}({params})"


@dataclass(frozen=True, slots=True)
class EventEntry:
    """Normalised view of an event ABI entry."""

    name: str
    inputs: tuple[AbiParameter, ...]
    anonymous: bool

    def __post_init__(self) -> None:
        if not self.name:
            msg = "Event ABI entries must include a name"
            raise ValueError(msg)

    @property
    def signature(self) -> str:
        params = ",".join(param.canonical for param in self.inputs)
        return f"{self.name}({params})"


@dataclass(frozen=True, slots=True)
class ConstructorEntry:
    """Normalised view of a constructor ABI entry."""

    inputs: tuple[AbiParameter, ...]
    state_mutability: str
    payable: bool

    @property
    def signature(self) -> str:
        params = ",".join(param.canonical for param in self.inputs)
        return f"constructor({params})"


@dataclass(frozen=True, slots=True)
class AbiSummary:
    """Container describing the high-level characteristics of an ABI."""

    constructor: ConstructorEntry | None
    functions: Mapping[str, tuple[FunctionEntry, ...]]
    events: Mapping[str, tuple[EventEntry, ...]]
    has_fallback: bool
    has_receive: bool

    def function_signatures(self) -> Mapping[str, tuple[str, ...]]:
        """Return the canonical signatures grouped by function name."""

        signatures: MutableMapping[str, tuple[str, ...]] = {}
        for name, group in self.functions.items():
            signatures[name] = tuple(entry.signature for entry in group)
        return MappingProxyType(dict(signatures))


def summarize_abi(abi: Sequence[Mapping[str, Any]]) -> AbiSummary:
    """Produce a lightweight summary of ``abi``.

    Parameters
    ----------
    abi:
        Iterable of ABI entry dictionaries as commonly returned by tooling such
        as ``solc --combined-json``.  Only the keys used in mainstream Ethereum
        contracts are required.
    """

    functions: MutableMapping[str, list[FunctionEntry]] = {}
    events: MutableMapping[str, list[EventEntry]] = {}
    constructor: ConstructorEntry | None = None
    has_fallback = False
    has_receive = False

    for raw in abi:
        entry_type = raw.get("type", "function")
        if entry_type == "function":
            function = _parse_function(raw)
            functions.setdefault(function.name, []).append(function)
        elif entry_type == "event":
            event = _parse_event(raw)
            events.setdefault(event.name, []).append(event)
        elif entry_type == "constructor":
            constructor = _parse_constructor(raw)
        elif entry_type == "fallback":
            has_fallback = True
        elif entry_type == "receive":
            has_receive = True
        else:  # pragma: no cover - ABI extensions we do not model
            continue

    normalized_functions = {
        name: tuple(sorted(entries, key=lambda item: item.signature))
        for name, entries in functions.items()
    }
    normalized_events = {
        name: tuple(sorted(entries, key=lambda item: item.signature))
        for name, entries in events.items()
    }

    return AbiSummary(
        constructor=constructor,
        functions=MappingProxyType(dict(normalized_functions)),
        events=MappingProxyType(dict(normalized_events)),
        has_fallback=has_fallback,
        has_receive=has_receive,
    )


def _parse_function(raw: Mapping[str, Any]) -> FunctionEntry:
    name = raw.get("name", "")
    inputs = _parse_parameters(raw.get("inputs", ()))
    outputs = _parse_parameters(raw.get("outputs", ()), prefix="ret")
    state_mutability = raw.get("stateMutability", _infer_state_mutability(raw))
    payable = bool(raw.get("payable", state_mutability == "payable"))
    constant = bool(
        raw.get(
            "constant",
            state_mutability in {"view", "pure"},
        )
    )
    return FunctionEntry(
        name=name,
        inputs=inputs,
        outputs=outputs,
        state_mutability=state_mutability,
        payable=payable,
        constant=constant,
    )


def _parse_event(raw: Mapping[str, Any]) -> EventEntry:
    name = raw.get("name", "")
    inputs = _parse_parameters(raw.get("inputs", ()))
    anonymous = bool(raw.get("anonymous", False))
    return EventEntry(name=name, inputs=inputs, anonymous=anonymous)


def _parse_constructor(raw: Mapping[str, Any]) -> ConstructorEntry:
    inputs = _parse_parameters(raw.get("inputs", ()))
    state_mutability = raw.get("stateMutability", _infer_state_mutability(raw))
    payable = bool(raw.get("payable", state_mutability == "payable"))
    return ConstructorEntry(inputs=inputs, state_mutability=state_mutability, payable=payable)


def _parse_parameters(entries: Iterable[Mapping[str, Any]], *, prefix: str = "arg") -> tuple[AbiParameter, ...]:
    params: list[AbiParameter] = []
    for index, raw in enumerate(entries):
        type_name = raw.get("type", "")
        name = raw.get("name") or f"{prefix}{index}"
        indexed = bool(raw.get("indexed", False))
        params.append(AbiParameter(name=name, type=type_name, indexed=indexed))
    return tuple(params)


def _infer_state_mutability(raw: Mapping[str, Any]) -> str:
    if raw.get("constant"):
        return "view"
    if raw.get("payable"):
        return "payable"
    return "nonpayable"
