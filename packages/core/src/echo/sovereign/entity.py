"""High level orchestration helpers for sovereign credential flows.

The production Echo stack already provides governance, donation, and
transparency helpers under :mod:`echo.sovereign`.  Several integration tests
need a light-weight coordination layer that models federated peers and
credential issuance without touching real networks.  The original prototype
for this orchestration lived in a standalone C++ snippet; this module provides
an idiomatic Python version that is easy to exercise inside the existing test
suite.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Deque, Dict, Iterable, List, Mapping, MutableMapping, Optional


@dataclass(frozen=True)
class DID:
    """Decentralized identifier descriptor used throughout the sovereign layer."""

    id: str
    public_key_pem: str
    private_key_pem: Optional[str] = None


@dataclass
class Credential:
    """Verifiable credential issued by the sovereign entity."""

    credential_id: str
    issuer: DID
    subject: DID
    claims: Dict[str, str]
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False

    def is_active(self, *, at: Optional[datetime] = None) -> bool:
        """Return ``True`` when the credential remains valid."""

        reference = at or datetime.now(timezone.utc)
        if self.revoked:
            return False
        return self.issued_at <= reference <= self.expires_at


@dataclass
class _Proposal:
    proposal_id: str
    description: str
    votes: Dict[str, bool] = field(default_factory=dict)
    enacted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Governance:
    """Thread-safe governance helper for managing upgrade proposals."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._proposals: MutableMapping[str, _Proposal] = {}

    def propose_upgrade(self, proposal_id: str, description: str) -> None:
        """Register a new proposal, enforcing unique identifiers."""

        if not proposal_id:
            raise ValueError("proposal_id must be provided")
        with self._lock:
            if proposal_id in self._proposals:
                raise ValueError(f"proposal '{proposal_id}' already exists")
            self._proposals[proposal_id] = _Proposal(proposal_id, description)

    def vote(self, proposal_id: str, voter: DID, approve: bool) -> bool:
        """Record a vote.  Returns ``True`` when the vote was accepted."""

        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                raise KeyError(f"unknown proposal '{proposal_id}'")
            if proposal.enacted:
                return False
            proposal.votes[voter.id] = approve
            return True

    def enact_upgrade(self, proposal_id: str) -> bool:
        """Mark a proposal as enacted when approvals outnumber rejections."""

        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                raise KeyError(f"unknown proposal '{proposal_id}'")
            if proposal.enacted:
                return True
            approvals = sum(1 for vote in proposal.votes.values() if vote)
            rejections = sum(1 for vote in proposal.votes.values() if not vote)
            if approvals == 0 or approvals <= rejections:
                raise ValueError("proposal lacks sufficient approvals to enact")
            proposal.enacted = True
            return True

    def proposal_snapshot(self) -> Dict[str, Dict[str, object]]:
        """Return a dictionary snapshot of proposal state for telemetry."""

        with self._lock:
            snapshot: Dict[str, Dict[str, object]] = {}
            for proposal_id, proposal in self._proposals.items():
                snapshot[proposal_id] = {
                    "description": proposal.description,
                    "votes": dict(proposal.votes),
                    "enacted": proposal.enacted,
                    "created_at": proposal.created_at,
                }
            return snapshot


class FederationNode:
    """Maintains an in-memory roster of peer nodes and broadcast events."""

    def __init__(self, node_id: DID) -> None:
        self.node_id = node_id
        self._lock = Lock()
        self._peers: Dict[str, DID] = {}
        self.broadcast_log: List[Dict[str, str]] = []

    def connect_peer(self, peer_id: DID) -> None:
        """Register a new peer if it has not already been connected."""

        with self._lock:
            self._peers.setdefault(peer_id.id, peer_id)

    def broadcast_event(self, event_type: str, payload: str) -> None:
        """Record a broadcast event for each peer.

        The real network layer would fan the payload out across TCP, gossip, or
        satellite transports.  For testing we simply capture the intent.
        """

        with self._lock:
            for peer in self._peers.values():
                self.broadcast_log.append(
                    {
                        "peer": peer.id,
                        "event_type": event_type,
                        "payload": payload,
                    }
                )


class CredentialIssuer:
    """Issues verifiable credentials scoped to a single sovereign DID."""

    def __init__(self, issuer_did: DID) -> None:
        self.issuer_did = issuer_did
        self._lock = Lock()
        self._issued: MutableMapping[str, Credential] = {}
        self._sequence = 0

    def issue_credential(
        self,
        subject: DID,
        claims: Mapping[str, str],
        *,
        valid_for: timedelta,
    ) -> Credential:
        """Issue and persist a credential for the supplied subject."""

        if valid_for <= timedelta(0):
            raise ValueError("valid_for must be positive")

        with self._lock:
            self._sequence += 1
            credential_id = f"{self.issuer_did.id}#{self._sequence:04d}"
            issued_at = datetime.now(timezone.utc)
            expires_at = issued_at + valid_for
            credential = Credential(
                credential_id=credential_id,
                issuer=self.issuer_did,
                subject=subject,
                claims=dict(claims),
                issued_at=issued_at,
                expires_at=expires_at,
            )
            self._issued[credential_id] = credential
            return credential

    def revoke_credential(self, credential_id: str) -> None:
        """Mark a credential as revoked if it exists."""

        with self._lock:
            credential = self._issued.get(credential_id)
            if credential is not None:
                credential.revoked = True

    def verify_credential(self, credential: Credential) -> bool:
        """Return ``True`` when the credential is active and was issued here."""

        with self._lock:
            stored = self._issued.get(credential.credential_id)
        if stored is None:
            return False
        if stored.issuer.id != self.issuer_did.id:
            return False
        return stored.is_active()

    def issued_credentials(self) -> Iterable[Credential]:
        with self._lock:
            return tuple(self._issued.values())


class SovereignEngine:
    """Coordinates governance, credential issuance, and federated broadcasts."""

    def __init__(self, core_did: DID) -> None:
        self.core_did = core_did
        self.federation = FederationNode(core_did)
        self.issuer = CredentialIssuer(core_did)
        self.governance = Governance()
        self._event_queue: Deque[tuple[str, Mapping[str, object]]] = deque()
        self.event_log: List[str] = []
        self.active = True

    def enqueue_event(self, event_type: str, payload: Mapping[str, object]) -> None:
        self._event_queue.append((event_type, dict(payload)))

    def run_event_loop(self, *, max_iterations: Optional[int] = None) -> None:
        """Process queued events synchronously for test environments."""

        processed = 0
        while self.active and self._event_queue:
            if max_iterations is not None and processed >= max_iterations:
                break
            event_type, payload = self._event_queue.popleft()
            self.on_network_event(event_type, payload)
            processed += 1

    def on_network_event(self, event_type: str, payload: Mapping[str, object]) -> Optional[Credential]:
        """Handle a network event captured by the sovereign node."""

        self.event_log.append(f"{event_type}:{payload}")
        if event_type != "Trigger_Credential_Issue":
            return None

        trigger_id = str(payload.get("trigger_id", "unknown"))
        subject = payload.get("subject")
        if isinstance(subject, DID):
            subject_did = subject
        elif isinstance(subject, Mapping):
            subject_did = DID(
                id=str(subject["id"]),
                public_key_pem=str(subject["public_key_pem"]),
                private_key_pem=subject.get("private_key_pem"),
            )
        else:
            raise ValueError("subject payload must be a DID or mapping")
        return self.issue_credential_for_trigger(trigger_id, subject_did)

    def issue_credential_for_trigger(self, trigger_id: str, subject: DID) -> Credential:
        """Issue a credential and broadcast the event."""

        claims = {
            "trigger_id": trigger_id,
            "issued_by": self.core_did.id,
        }
        credential = self.issuer.issue_credential(subject, claims, valid_for=timedelta(hours=1))
        self.event_log.append(
            f"Issued credential {credential.credential_id} to {subject.id} for trigger {trigger_id}"
        )
        self.federation.broadcast_event("Credential_Issued", credential.credential_id)
        return credential

