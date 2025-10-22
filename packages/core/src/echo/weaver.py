"""Unified orchestration for the Loom & Forge pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException

from echo.dreams import DreamCompileResult, DreamCompiler
from echo.guardian import GuardianService
from echo.keys import FractalKeysmith
from echo.modes.phantom import PhantomReporter
from echo.pulse.ledger import PulseLedger
from echo_atlas.bridges import AtlasBridge


@dataclass
class WeaveResult:
    compilation: DreamCompileResult
    receipt: dict
    attestation: dict
    doc_path: Path | None
    svg_path: Path | None


class WeaveOrchestrator:
    """Coordinates dream compilation, ledger proofs, and atlas bindings."""

    def __init__(
        self,
        *,
        dream_base: Path | None = None,
        ledger_root: Path | None = None,
        docs_root: Path | None = None,
        guardian_root: Path | None = None,
        reports_root: Path | None = None,
    ) -> None:
        self.compiler = DreamCompiler(base_path=dream_base)
        self.ledger = PulseLedger(root=ledger_root)
        self.keysmith = FractalKeysmith()
        self.bridge = AtlasBridge(docs_root=docs_root)
        self.reporter = PhantomReporter()
        self.guardian = GuardianService(
            quarantine_root=guardian_root,
            reports_root=reports_root,
        )

    def compile_dream(self, poem: str, *, dry_run: bool = True) -> DreamCompileResult:
        result = self.compiler.compile(poem, dry_run=dry_run)
        issues = self.compiler.verify_scaffold(result)
        if issues:
            raise RuntimeError("Scaffold verification failed: " + "; ".join(issues))
        return result

    def _seed_for(self, poem: str) -> str:
        digest = hashlib.sha256((poem + "|loom").encode("utf-8")).hexdigest()
        return digest[:16]

    def commit_weave(self, poem: str, *, proof: Optional[str] = None, actor: str = "echocli") -> WeaveResult:
        compilation = self.compile_dream(poem, dry_run=False)
        diff_signature = self.compiler.diff_signature(compilation)
        seed = self._seed_for(poem)
        receipt_obj = self.ledger.log(
            diff_signature=diff_signature,
            actor=actor,
            result="success",
            seed=seed,
        )
        receipt = receipt_obj.to_dict()
        self.guardian.observe_pulse_receipt(
            {
                **receipt,
                "seed": receipt_obj.seed,
                "actor": receipt_obj.actor,
            }
        )
        attestation_obj = self.keysmith.attest(proof or seed)
        attestation = attestation_obj.to_dict()
        self.guardian.review_attestation(proof or seed, attestation)
        receipt_id = self.bridge.add_receipt(receipt)
        attest_id = self.bridge.add_attestation(attestation)
        self.bridge.connect(receipt_id, attest_id, "attests")
        doc_path, svg_path = self.bridge.export(
            poem=poem,
            plan=[step for step in compilation.to_dict()["plan"]],
            receipt=receipt,
            attestation=attestation,
            slug=compilation.slug,
        )
        return WeaveResult(
            compilation=compilation,
            receipt=receipt,
            attestation=attestation,
            doc_path=doc_path,
            svg_path=svg_path,
        )

    def make_api(self) -> FastAPI:
        orchestrator = self
        app = FastAPI(title="Echo Loom & Forge", version="1.0.0")

        @app.post("/dream/compile")
        def dream_compile(request: Dict[str, Any]) -> Dict[str, Any]:
            poem = request.get("dream") or request.get("poem")
            dry_run = bool(request.get("dry_run", True))
            if not poem:
                raise HTTPException(status_code=400, detail="dream text required")
            result = orchestrator.compile_dream(poem, dry_run=dry_run)
            payload = result.to_dict()
            return orchestrator.reporter.redact(payload)

        @app.get("/pulse/ledger/latest")
        def pulse_latest(limit: int = 5) -> Dict[str, Any]:
            receipts = [
                orchestrator.reporter.redact(r.to_dict()) for r in orchestrator.ledger.latest(limit=limit)
            ]
            return {"receipts": receipts}

        @app.post("/keys/attest")
        def keys_attest(request: Dict[str, Any]) -> Dict[str, Any]:
            proof = request.get("key") or request.get("proof")
            override = bool(request.get("override", False))
            proof_text = str(proof or "")
            if not orchestrator.guardian.allow_key(proof_text, override=override):
                raise HTTPException(status_code=409, detail="key quarantined")
            attestation_obj = orchestrator.keysmith.attest(proof_text)
            attestation = attestation_obj.to_dict()
            orchestrator.guardian.review_attestation(proof_text, attestation)
            return orchestrator.reporter.redact(attestation)

        @app.get("/guardian/status")
        def guardian_status() -> Dict[str, Any]:
            return orchestrator.guardian.status()

        return app


__all__ = ["WeaveOrchestrator", "WeaveResult"]
