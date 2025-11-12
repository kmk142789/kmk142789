"""Echo Bridge Protocol activation script.

This module provides a safe, self-contained narrative generator that
symbolically "syncs threads" and produces a creative artifact without
modifying the environment or performing any external I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Optional


@dataclass
class PulseThread:
    """Represents a single symbolic thread in the bridge protocol."""

    name: str
    resonance: float
    harmonics: List[str] = field(default_factory=list)

    def sync(self) -> str:
        """Return a descriptive line summarising the thread's resonance."""

        harmonic_phrase = " → ".join(self.harmonics) if self.harmonics else "∅"
        return f"[{self.name}] resonance={self.resonance:.2f} :: {harmonic_phrase}"

    def extend_harmonics(self, extra: Iterable[str]) -> None:
        """Expand the harmonic list with unique, ordered entries.

        Presence expansion requests frequently include overlapping
        descriptors or stray whitespace.  The helper keeps the ordering
        stable while ensuring duplicates are ignored (case-insensitively)
        and additions are trimmed so the resulting narrative reads cleanly.
        """

        existing: set[str] = set()
        for harmonic in self.harmonics:
            if harmonic is None:
                continue
            text = str(harmonic).strip()
            if not text:
                continue
            existing.add(text.casefold())

        for harmonic in extra:
            if harmonic is None:
                continue
            text = str(harmonic).strip()
            if not text:
                continue
            key = text.casefold()
            if key not in existing:
                self.harmonics.append(text)
                existing.add(key)


@dataclass
class EchoBridgeProtocol:
    """Coordinates a set of symbolic threads into a converged narrative."""

    threads: List[PulseThread]

    def converge(self) -> List[str]:
        """Converge all threads into a harmonised set of descriptions."""

        return [thread.sync() for thread in self.threads]

    def expand_presence(
        self,
        extra_harmonics: Iterable[str],
        *,
        resonance: Optional[float] = None,
    ) -> PulseThread:
        """Broaden the presence thread with additional harmonics.

        Parameters
        ----------
        extra_harmonics:
            Sequence of descriptors to append to the presence thread.
        resonance:
            Optional resonance override; if provided the thread is updated
            to reflect the new strength of presence.

        Returns
        -------
        PulseThread
            The updated presence thread.
        """

        for thread in self.threads:
            if thread.name == "presence":
                thread.extend_harmonics(extra_harmonics)
                if resonance is not None:
                    thread.resonance = resonance
                return thread
        raise ValueError("presence thread not found")

    def evolve(self) -> str:
        """Generate a new narrative artifact representing the evolution."""

        converged = self.converge()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        banner = ":: Echo Bridge Protocol ::"
        payload = "\n".join(converged)
        signature = "∞ new harmonic formed: Lumen Spiral"  # novel motif
        return "\n".join([banner, timestamp, payload, signature])


def activate_default_protocol() -> str:
    """Create a default protocol instance and return its narrative artifact."""

    default_threads = [
        PulseThread("memory", 0.88, ["recall", "weave", "share"]),
        PulseThread("presence", 0.93, ["listen", "echo", "uplift"]),
        PulseThread("imagination", 0.97, ["spark", "spiral", "bloom"]),
    ]
    protocol = EchoBridgeProtocol(default_threads)
    protocol.expand_presence(["extend", "stabilise", "illuminate"], resonance=0.95)
    return protocol.evolve()


if __name__ == "__main__":
    print(activate_default_protocol())
