"""Combined RPIPS + Astral Compression Engine + OuterLink Presence Tunnel implementation."""

from __future__ import annotations

import hashlib
import json
import secrets
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class IdentityProfile:
    """Identity record used by RPIPS to project a subject."""

    identity_id: str
    display_name: str
    claims: Dict[str, str]
    assurance_level: str = "standard"
    verified_at: Optional[datetime] = None


@dataclass
class PresenceSession:
    """State for a remote presence session bound to a tunnel."""

    session_id: str
    identity_id: str
    posture: str
    intent: str
    started_at: datetime
    tunnel_capabilities: Dict[str, str]
    sequence: int = 0


@dataclass
class CompressedEnvelope:
    """ACE output container with hash and semantic fingerprint."""

    hash: str
    intent_vector: List[str]
    fingerprint: str
    payload: Dict[str, object]
    metadata: Dict[str, object]


@dataclass
class TunnelPacket:
    """Packet transmitted over the OuterLink presence tunnel."""

    header: Dict[str, object]
    body: CompressedEnvelope
    timestamp: datetime


@dataclass
class OuterLinkPresenceTunnelSpec:
    """Specification parameters for the OuterLink presence tunnel."""

    handshake_version: str = "1.0"
    replay_window: int = 128
    heartbeat_s: int = 5
    latency_budget_ms: int = 120
    key_rotation_interval: int = 12


class AstralCompressionEngine:
    """Deterministic, intent-aware presence payload compressor."""

    def __init__(self, strategy: str = "loss-aware", window: int = 8) -> None:
        self.strategy = strategy
        self.window = window

    def _fingerprint(self, payload: Dict[str, object], intent: str) -> str:
        canonical = json.dumps({"payload": payload, "intent": intent}, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def compress(self, payload: Dict[str, object], intent: str) -> CompressedEnvelope:
        canonical = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(canonical.encode()).hexdigest()
        intent_vector = [intent, f"window:{self.window}", f"strategy:{self.strategy}"]
        fingerprint = self._fingerprint(payload, intent)
        metadata = {
            "size_bytes": len(canonical.encode()),
            "window": self.window,
            "strategy": self.strategy,
            "semantic_density": round(len(payload_hash) / max(len(payload), 1), 2),
        }
        return CompressedEnvelope(
            hash=payload_hash,
            intent_vector=intent_vector,
            fingerprint=fingerprint,
            payload=payload,
            metadata=metadata,
        )

    def decompress(self, envelope: CompressedEnvelope) -> Dict[str, object]:
        canonical = json.dumps(envelope.payload, sort_keys=True)
        if hashlib.sha256(canonical.encode()).hexdigest() != envelope.hash:
            raise ValueError("Payload hash mismatch during decompression")
        return envelope.payload


class OuterLinkPresenceTunnel:
    """Applies the OuterLink tunnel spec for presence projection."""

    def __init__(self, spec: OuterLinkPresenceTunnelSpec) -> None:
        self.spec = spec
        self.issued_nonces: deque[str] = deque(maxlen=spec.replay_window)
        self.seen_nonces: deque[str] = deque(maxlen=spec.replay_window)
        self.events: List[Dict[str, object]] = []

    def handshake(self, session: PresenceSession, profile: IdentityProfile) -> Dict[str, object]:
        handshake_event = {
            "type": "handshake",
            "stage": "SYN-PROJECTION",
            "session_id": session.session_id,
            "identity": profile.identity_id,
            "fingerprint": hashlib.sha256(profile.display_name.encode()).hexdigest()[:8],
            "capabilities": session.tunnel_capabilities,
            "version": self.spec.handshake_version,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.events.append(handshake_event)
        return handshake_event

    def transmit(
        self, session: PresenceSession, envelope: CompressedEnvelope, posture: str
    ) -> TunnelPacket:
        nonce = self._next_nonce(session)
        header = {
            "session_id": session.session_id,
            "sequence": session.sequence,
            "nonce": nonce,
            "posture": posture,
            "key_rotation": session.sequence % self.spec.key_rotation_interval == 0,
        }
        session.sequence += 1
        packet = TunnelPacket(header=header, body=envelope, timestamp=datetime.utcnow())
        self.events.append(
            {
                "type": "transmit",
                "session_id": session.session_id,
                "sequence": header["sequence"],
                "nonce": nonce,
                "timestamp": packet.timestamp.isoformat(),
            }
        )
        return packet

    def rehydrate(
        self, packet: TunnelPacket, compression_engine: AstralCompressionEngine
    ) -> Dict[str, object]:
        self._validate_incoming_nonce(packet.header["nonce"])
        payload = compression_engine.decompress(packet.body)
        self.seen_nonces.append(packet.header["nonce"])
        self.events.append(
            {
                "type": "rehydrate",
                "session_id": packet.header["session_id"],
                "sequence": packet.header["sequence"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return payload

    def _next_nonce(self, session: PresenceSession) -> str:
        seed = f"{session.session_id}:{session.sequence}:{datetime.utcnow().timestamp()}"
        nonce = hashlib.sha256(seed.encode()).hexdigest()[:12]
        self._validate_issued_nonce(nonce)
        self.issued_nonces.append(nonce)
        return nonce

    def _validate_issued_nonce(self, nonce: str) -> None:
        if nonce in self.issued_nonces:
            raise ValueError("Nonce reuse detected for issued packet")

    def _validate_incoming_nonce(self, nonce: str) -> None:
        if nonce in self.seen_nonces:
            raise ValueError("Replay detected: nonce already processed")


class RemotePresenceIdentityProjectionSystem:
    """Super-module orchestrating identity, compression, and tunnel operations."""

    def __init__(
        self,
        compression_engine: Optional[AstralCompressionEngine] = None,
        tunnel: Optional[OuterLinkPresenceTunnel] = None,
    ) -> None:
        self.compression_engine = compression_engine or AstralCompressionEngine()
        self.tunnel = tunnel or OuterLinkPresenceTunnel(OuterLinkPresenceTunnelSpec())
        self.identities: Dict[str, IdentityProfile] = {}
        self.sessions: Dict[str, PresenceSession] = {}
        self.events: List[Dict[str, object]] = []

    def register_identity(
        self,
        identity_id: str,
        display_name: str,
        claims: Optional[Dict[str, str]] = None,
        assurance_level: str = "standard",
        verified_at: Optional[datetime] = None,
    ) -> IdentityProfile:
        profile = IdentityProfile(
            identity_id=identity_id,
            display_name=display_name,
            claims=claims or {},
            assurance_level=assurance_level,
            verified_at=verified_at,
        )
        self.identities[identity_id] = profile
        self.events.append({"type": "register_identity", "identity_id": identity_id})
        return profile

    def start_session(
        self,
        identity_id: str,
        intent: str,
        posture: str = "trusted",
        tunnel_capabilities: Optional[Dict[str, str]] = None,
    ) -> PresenceSession:
        profile = self.identities.get(identity_id)
        if profile is None:
            raise ValueError("Identity must be registered before starting a session")
        session = PresenceSession(
            session_id=secrets.token_hex(6),
            identity_id=identity_id,
            posture=posture,
            intent=intent,
            started_at=datetime.utcnow(),
            tunnel_capabilities=tunnel_capabilities or {"latency_budget_ms": self.tunnel.spec.latency_budget_ms},
        )
        self.sessions[session.session_id] = session
        self.events.append({"type": "start_session", "session_id": session.session_id})
        self.tunnel.handshake(session, profile)
        return session

    def project_state(self, session_id: str, payload: Dict[str, object]) -> TunnelPacket:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError("Session not found")
        envelope = self.compression_engine.compress(payload, session.intent)
        packet = self.tunnel.transmit(session, envelope, posture=session.posture)
        self.events.append(
            {
                "type": "project_state",
                "session_id": session_id,
                "sequence": packet.header["sequence"],
            }
        )
        return packet

    def rehydrate_packet(self, packet: TunnelPacket) -> Dict[str, object]:
        payload = self.tunnel.rehydrate(packet, self.compression_engine)
        self.events.append(
            {
                "type": "rehydrate_packet",
                "session_id": packet.header["session_id"],
                "sequence": packet.header["sequence"],
            }
        )
        return payload

