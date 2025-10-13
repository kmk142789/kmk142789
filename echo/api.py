"""FastAPI integration layer for Echo verification."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from memory import PersistentMemoryStore

app = FastAPI(title="Echo Verification API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = PersistentMemoryStore.load_default()
KNOWN_DATASET_PATHS = [
    Path("pulse.json"),
    Path("pulse_history.json"),
    Path("manifest/index.json"),
]


class VerificationRequest(BaseModel):
    dataset_path: Optional[str] = Field(
        None, description="Path to a dataset file whose fingerprint should be validated."
    )
    dataset_text: Optional[str] = Field(
        None, description="Inline dataset contents to fingerprint and validate."
    )
    key: Optional[str] = Field(None, description="Key or secret material to validate.")


class VerificationResponse(BaseModel):
    timestamp: str
    dataset_sha: Optional[str]
    dataset_size: Optional[int]
    parsed_entries: Optional[int]
    matched_dataset: Optional[str]
    warnings: list[str]
    validations: Dict[str, Dict[str, object]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _fingerprint_bytes(payload: bytes) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(payload)
    return digest.hexdigest()


def _fingerprint_path(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return _fingerprint_bytes(path.read_bytes())


def _parse_dataset(data: bytes) -> Tuple[bool, Optional[int], list[str], Dict[str, object]]:
    warnings: list[str] = []
    details: Dict[str, object] = {}
    try:
        parsed = json.loads(data.decode("utf-8"))
        details["type"] = type(parsed).__name__
        if isinstance(parsed, dict):
            entries = len(parsed)
        elif isinstance(parsed, list):
            entries = len(parsed)
        else:
            entries = 1
        return True, entries, warnings, details
    except UnicodeDecodeError:
        warnings.append("dataset payload is not UTF-8; treating as binary")
    except json.JSONDecodeError as exc:
        warnings.append(f"dataset JSON parse failed: {exc.msg}")

    try:
        text = data.decode("utf-8", errors="ignore")
    except UnicodeDecodeError:
        return False, None, warnings, details

    lines = [line for line in (line.strip() for line in text.splitlines()) if line]
    if lines:
        details["line_sample"] = lines[:5]
        warnings.append("dataset treated as line-delimited text")
        return False, len(lines), warnings, details
    return False, None, warnings, details


def _validate_key_material(key: Optional[str]) -> Tuple[bool, str]:
    if key is None:
        return True, "no key supplied"
    key_stripped = key.strip()
    if len(key_stripped) < 8:
        return False, "key length must be at least 8 characters"
    if key_stripped.islower() or key_stripped.isupper():
        return False, "key should mix character cases for resilience"
    if not any(char.isdigit() for char in key_stripped):
        return False, "key should include at least one digit"
    return True, "key passes heuristic validation"


@app.post("/api/verify", response_model=VerificationResponse)
def verify(request: VerificationRequest) -> VerificationResponse:
    if not (request.dataset_path or request.dataset_text or request.key):
        raise HTTPException(
            status_code=400,
            detail="Provide dataset_path, dataset_text, or key for verification.",
        )

    dataset_bytes = b""
    dataset_source = None
    dataset_sha: Optional[str] = None
    dataset_size: Optional[int] = None
    parsed_entries: Optional[int] = None
    warnings: list[str] = []
    matched_dataset: Optional[str] = None

    if request.dataset_path:
        path = Path(request.dataset_path).expanduser()
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {path}")
        dataset_bytes = path.read_bytes()
        dataset_source = str(path)
    elif request.dataset_text is not None:
        dataset_bytes = request.dataset_text.encode("utf-8")
        dataset_source = "inline-text"

    dataset_details: Dict[str, object] = {}
    if dataset_bytes:
        dataset_size = len(dataset_bytes)
        dataset_sha = _fingerprint_bytes(dataset_bytes)
        parsed, entries, parse_warnings, parse_details = _parse_dataset(dataset_bytes)
        warnings.extend(parse_warnings)
        parsed_entries = entries
        dataset_details = parse_details

        for path in KNOWN_DATASET_PATHS:
            known_sha = _fingerprint_path(path)
            if known_sha and known_sha == dataset_sha:
                matched_dataset = str(path)
                break
    else:
        warnings.append("no dataset supplied for fingerprinting")

    key_ok, key_message = _validate_key_material(request.key)

    validations = {
        "key_check": {"status": "passed" if key_ok else "failed", "message": key_message},
    }
    if dataset_bytes:
        validations["dataset_parse"] = {
            "status": "passed" if parsed_entries is not None else "failed",
            "details": dataset_details,
        }
    else:
        validations["dataset_parse"] = {
            "status": "failed",
            "details": {"reason": "no dataset provided"},
        }

    timestamp = _utc_now()
    with store.context(
        "api.verify",
        {
            "dataset_source": dataset_source,
            "has_dataset": bool(dataset_bytes),
            "has_key": request.key is not None,
        },
    ) as session:
        session.log_command(
            "verify_request",
            {
                "dataset_source": dataset_source,
                "dataset_size": dataset_size,
                "has_key": request.key is not None,
            },
        )
        if dataset_sha:
            session.log_dataset(
                "api_dataset", dataset_sha, source=dataset_source or "unknown", size=dataset_size
            )
        session.log_validation("key_check", key_ok, {"message": key_message})
        session.log_validation(
            "dataset_parse",
            parsed_entries is not None,
            {"entries": parsed_entries, "details": dataset_details},
        )
        for warning in warnings:
            session.add_warning(warning)
        session.set_summary(
            {
                "dataset_sha": dataset_sha,
                "parsed_entries": parsed_entries,
                "matched_dataset": matched_dataset,
            }
        )

    response = VerificationResponse(
        timestamp=timestamp,
        dataset_sha=dataset_sha,
        dataset_size=dataset_size,
        parsed_entries=parsed_entries,
        matched_dataset=matched_dataset,
        warnings=warnings,
        validations=validations,
    )
    return response


def _run_self_test() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    payload = {"dataset_text": "{\"hello\": \"world\"}", "key": "EchoKey123"}
    response = client.post("/api/verify", json=payload)
    response.raise_for_status()
    data = response.json()
    print("Self-test verification:", json.dumps(data, indent=2))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Echo Verification API")
    parser.add_argument("--host", default=os.getenv("ECHO_API_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("ECHO_API_PORT", "8000")))
    parser.add_argument("--self-test", action="store_true", help="Execute a built-in smoke test")
    args = parser.parse_args(argv)

    if args.self_test:
        _run_self_test()
        return 0

    import uvicorn

    uvicorn.run("echo.api:app", host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
