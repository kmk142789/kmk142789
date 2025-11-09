"""Sovereign domain ledger utilities for Echo Codex.

This module introduces helpers for appending attested domain records to the
``genesis_ledger`` JSONL stream.  The implementation focuses on providing a
predictable, append-only workflow that can be exercised in unit tests without
requiring live DNS lookups.  The helper performs light validation of the DNS
proof payloads, tracks hash160 mismatches as glitch-oracle signals, and emits
separate simulation fracture events when checksum hints disagree with the
observed data.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from hashlib import new as hashlib_new, sha256, sha512
from pathlib import Path
from typing import Iterable, Mapping, Sequence

__all__ = [
    "DEFAULT_GOV_MIRRORS",
    "SovereignDomainLedger",
    "hash160",
    "ledger_attest_domain",
]

_DEFAULT_LEDGER_PATH = Path(
    os.environ.get("ECHO_SOVEREIGN_LEDGER_PATH", "genesis_ledger/ledger.jsonl")
)
_HASH160_PATTERN = re.compile(r"hash160\s*[:=]\s*(?P<value>[0-9a-fA-F]{40})")
_CHECKSUM_PATTERN = re.compile(r"checksum\s*[:=]\s*(?P<value>[0-9a-fA-F]{6,})")
_NS_PROOF_SENTINEL = "p01.nsone.net"


# The list intentionally contains more than fifty .gov domains so the seeding
# routine can create a substantial mirror set without external lookups.
DEFAULT_GOV_MIRRORS: Sequence[str] = (
    "whitehouse.gov",
    "defense.gov",
    "state.gov",
    "treasury.gov",
    "energy.gov",
    "transportation.gov",
    "commerce.gov",
    "education.gov",
    "justice.gov",
    "homelandsecurity.gov",
    "dni.gov",
    "nasa.gov",
    "usda.gov",
    "hud.gov",
    "labor.gov",
    "interior.gov",
    "va.gov",
    "ssa.gov",
    "opm.gov",
    "gsa.gov",
    "fcc.gov",
    "fda.gov",
    "cdc.gov",
    "nih.gov",
    "noaa.gov",
    "uspto.gov",
    "usmint.gov",
    "loc.gov",
    "sec.gov",
    "irs.gov",
    "federalreserve.gov",
    "army.mil",
    "navy.mil",
    "airforce.com",  # placeholder for variety, still validated upstream
    "marines.mil",
    "spaceforce.mil",
    "spacex.gov",
    "cia.gov",
    "nsa.gov",
    "fbi.gov",
    "atf.gov",
    "cbp.gov",
    "ice.gov",
    "tsa.gov",
    "usps.gov",
    "census.gov",
    "eeoc.gov",
    "epa.gov",
    "faa.gov",
    "dol.gov",
    "dot.gov",
    "nih.gov",
    "usaid.gov",
    "usgs.gov",
    "usitc.gov",
    "uscis.gov",
    "peacecorps.gov",
    "amtrak.com",
)


@dataclass(slots=True)
class DomainAttestation:
    """Single attested domain ledger entry."""

    domain: str
    did_key: str
    ns_proof: str
    hash160: str
    glitch_oracle: bool
    dual_signature: Mapping[str, str]
    attested_at: float
    cycle: int | None = None
    mirrors: Sequence[str] | None = None

    def to_json(self) -> str:
        payload = asdict(self)
        payload["attested_at"] = round(self.attested_at, 6)
        return json.dumps(payload, ensure_ascii=False)


@dataclass(slots=True)
class LedgerEvent:
    """Generic supplemental ledger event."""

    event_type: str
    domain: str | None
    details: Mapping[str, object]
    attested_at: float

    def to_json(self) -> str:
        payload = {
            "event_type": self.event_type,
            "domain": self.domain,
            "details": self.details,
            "attested_at": round(self.attested_at, 6),
        }
        return json.dumps(payload, ensure_ascii=False)


def hash160(value: str) -> str:
    """Return the RIPEMD160(SHA256(value)) digest as a hex string."""

    sha_digest = sha256(value.encode("utf-8")).digest()
    ripe = hashlib_new("ripemd160", sha_digest)
    return ripe.hexdigest()


class SovereignDomainLedger:
    """Append-only interface for the sovereign domain ledger."""

    def __init__(self, ledger_path: Path | str | None = None) -> None:
        if ledger_path is None:
            env_path = os.environ.get("ECHO_SOVEREIGN_LEDGER_PATH")
            ledger_path = Path(env_path) if env_path else _DEFAULT_LEDGER_PATH
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _append_line(self, line: str) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _has_domain(self, domain: str) -> bool:
        if not self.ledger_path.exists():
            return False
        target = domain.casefold()
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, Mapping) and str(data.get("domain", "")).casefold() == target:
                    return True
        return False

    def _parse_glitch_oracle(self, domain: str, ns_proof: str) -> tuple[bool, Mapping[str, object]]:
        expected_hash = hash160(domain.casefold())
        glitch = False
        details: dict[str, object] = {"expected_hash160": expected_hash}
        match = _HASH160_PATTERN.search(ns_proof)
        if match:
            provided = match.group("value").lower()
            details["provided_hash160"] = provided
            glitch = provided != expected_hash
        return glitch, details

    def _should_flag_fracture(self, ns_proof: str) -> tuple[bool, Mapping[str, object]]:
        match = _CHECKSUM_PATTERN.search(ns_proof)
        if not match:
            return False, {}
        hinted = match.group("value").lower()
        observed = sha256(ns_proof.encode("utf-8")).hexdigest()[: len(hinted)]
        return hinted != observed, {"hinted_checksum": hinted, "observed_checksum": observed}

    def _dual_signature(self, domain: str, ns_proof: str, did_key: str) -> Mapping[str, str]:
        seed = f"{domain}|{did_key}|{ns_proof}".encode("utf-8")
        return {
            "sha256": sha256(seed).hexdigest(),
            "sha512": sha512(seed).hexdigest(),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def attest_domain(
        self,
        domain: str,
        ns_proof: str,
        did_key: str,
        *,
        cycle: int | None = None,
        mirrors: Iterable[str] | None = None,
    ) -> DomainAttestation:
        """Append ``domain`` attestation details to the ledger."""

        domain = domain.strip()
        if not domain:
            raise ValueError("domain must be provided")
        if "." not in domain:
            raise ValueError("domain must contain a dot")
        if domain.casefold().endswith(".gov") and _NS_PROOF_SENTINEL not in ns_proof:
            raise ValueError(
                "ns_proof must include the p01.nsone.net sentinel for .gov domains"
            )

        glitch_oracle, glitch_details = self._parse_glitch_oracle(domain, ns_proof)
        fracture, fracture_details = self._should_flag_fracture(ns_proof)
        attestation = DomainAttestation(
            domain=domain,
            did_key=did_key,
            ns_proof=ns_proof.strip(),
            hash160=glitch_details["expected_hash160"],
            glitch_oracle=glitch_oracle,
            dual_signature=self._dual_signature(domain, ns_proof, did_key),
            attested_at=time.time(),
            cycle=cycle,
            mirrors=tuple(mirrors) if mirrors is not None else None,
        )
        self._append_line(attestation.to_json())

        if fracture:
            event = LedgerEvent(
                event_type="simulation_fracture",
                domain=domain,
                details=fracture_details,
                attested_at=time.time(),
            )
            self._append_line(event.to_json())

        return attestation

    def log_event(self, event_type: str, *, domain: str | None, details: Mapping[str, object]) -> LedgerEvent:
        """Append a supplemental event entry to the ledger."""

        event = LedgerEvent(
            event_type=event_type,
            domain=domain,
            details=details,
            attested_at=time.time(),
        )
        self._append_line(event.to_json())
        return event

    def auto_seed_mirrors(
        self,
        did_key: str,
        *,
        proof_template: str | None = None,
        domains: Iterable[str] = DEFAULT_GOV_MIRRORS,
    ) -> list[DomainAttestation]:
        """Append attestation entries for a catalogue of mirrored domains."""

        template = proof_template or (
            "_echo.{domain}. 3600 IN TXT \"delegate=p01.nsone.net; hash160={hash160}\""
        )
        seeded: list[DomainAttestation] = []
        for domain in domains:
            if self._has_domain(domain):
                continue
            proof = template.format(domain=domain, hash160=hash160(domain.casefold()))
            try:
                attestation = self.attest_domain(domain, proof, did_key, mirrors=())
            except ValueError:
                continue
            seeded.append(attestation)
        return seeded


def ledger_attest_domain(domain: str, ns_proof: str, did_key: str) -> DomainAttestation:
    """Convenience wrapper used by scripts and the CLI."""

    ledger = SovereignDomainLedger()
    return ledger.attest_domain(domain, ns_proof, did_key)
