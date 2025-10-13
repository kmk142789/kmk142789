"""FastAPI service that verifies EchoEvolver runs and records them to memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .api import capability_router, receipt_router
from .memory import JsonMemoryStore


class ValidationPayload(BaseModel):
    name: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


class VerificationRequest(BaseModel):
    commands: List[str] = Field(default_factory=list)
    dataset_paths: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of dataset labels to absolute or relative file paths.",
    )
    validations: List[ValidationPayload] = Field(default_factory=list)
    github_repo: Optional[str] = Field(
        default=None, description="Optional GitHub repository for deployment hook."
    )
    firebase_project: Optional[str] = Field(
        default=None, description="Optional Firebase project for deployment hook."
    )


class VerificationResponse(BaseModel):
    recorded_commands: List[str]
    dataset_fingerprints: Dict[str, Dict[str, Any]]
    validations: List[Dict[str, Any]]
    hooks: List[str]


def create_app(memory_store: Optional[JsonMemoryStore] = None) -> FastAPI:
    """Create the FastAPI verification service."""

    store = memory_store or JsonMemoryStore()
    app = FastAPI(title="Echo Verification Service", version="1.0.0")
    app.include_router(capability_router)
    app.include_router(receipt_router)

    @app.post("/api/verify", response_model=VerificationResponse)
    async def verify(request: VerificationRequest) -> VerificationResponse:
        with store.session(metadata={"source": "api.verify"}) as session:
            recorded = []
            for command in request.commands:
                session.record_command(command, detail="api-submitted")
                recorded.append(command)

            dataset_paths = request.dataset_paths or {
                name: str(path) for name, path in store.core_datasets.items()
            }
            for label, dataset in dataset_paths.items():
                dataset_path = Path(dataset)
                session.fingerprint_dataset(label, dataset_path)

            for payload in request.validations:
                session.record_validation(payload.name, payload.status, details=payload.details)

            hooks: List[str] = []
            if request.github_repo:
                hooks.append(f"GitHub deployment prepared for {request.github_repo}")
            if request.firebase_project:
                hooks.append(f"Firebase deploy hook primed for {request.firebase_project}")
            if hooks:
                session.annotate(deployment_hooks=hooks)

            store.fingerprint_core_datasets(session)

        return VerificationResponse(
            recorded_commands=recorded,
            dataset_fingerprints=session.dataset_fingerprints,
            validations=session.validations,
            hooks=hooks,
        )

    return app


app = create_app()
