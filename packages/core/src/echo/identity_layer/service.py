"""Cross-platform service interfaces for the identity layer."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import grpc
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .proto import identity_pb2, identity_pb2_grpc
from .vault import EncryptedIdentityVault, VaultEvent


@dataclass
class IdentityLayerConfig:
    """Configuration for the identity layer services."""

    vault_root: Path
    passphrase: str
    host: str = "127.0.0.1"
    json_rpc_port: int = 8545
    grpc_port: int = 8546


class _JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class _JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any = None
    id: Optional[Any]


class IdentityService:
    """Facade that exposes JSON-RPC and gRPC front-ends for the vault."""

    def __init__(self, config: IdentityLayerConfig) -> None:
        self._config = config
        self._vault = EncryptedIdentityVault(config.vault_root, config.passphrase)
        self._app = self._build_fastapi()
        self._grpc_server: Optional[grpc.aio.Server] = None

    @property
    def vault(self) -> EncryptedIdentityVault:
        return self._vault

    def fastapi_app(self) -> FastAPI:
        return self._app

    def _build_fastapi(self) -> FastAPI:
        app = FastAPI(title="Echo Identity Layer", version="1.0.0")

        @app.post("/rpc")
        async def rpc_handler(request: _JsonRpcRequest) -> JSONResponse:  # type: ignore[misc]
            if request.jsonrpc != "2.0":
                raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")
            method = request.method
            params = request.params or {}
            handlers = {
                "list_keys": self._rpc_list_keys,
                "ensure_key": self._rpc_ensure_key,
                "rotate": self._rpc_rotate,
                "sign": self._rpc_sign,
                "history": self._rpc_history,
            }
            if method not in handlers:
                raise HTTPException(status_code=404, detail=f"Unknown method {method}")
            result = handlers[method](**params)
            response = _JsonRpcResponse(result=result, id=request.id)
            return JSONResponse(response.model_dump())

        return app

    # ------------------------------------------------------------------
    # JSON-RPC method implementations
    # ------------------------------------------------------------------
    def _rpc_list_keys(self) -> Any:
        return [self._format_key(k) for k in self._vault.list_keys()]

    def _rpc_ensure_key(
        self,
        *,
        chain: str,
        account: int,
        index: int,
        change: int = 0,
        origin: str,
        platform: Optional[str] = None,
    ) -> Any:
        key = self._vault.ensure_key(
            chain=chain,
            account=account,
            index=index,
            change=change,
            origin=origin,
            platform_name=platform,
        )
        return self._format_key(key)

    def _rpc_rotate(
        self,
        *,
        chain: str,
        account: int,
        index: int,
        change: int = 0,
        origin: str,
    ) -> Any:
        key = self._vault.rotate(chain=chain, account=account, index=index, change=change, origin=origin)
        return self._format_key(key)

    def _rpc_sign(self, *, did: str, message_b64: str) -> Any:
        signature = self._vault.sign(did, base64.b64decode(message_b64))
        return {"signature_b64": base64.b64encode(signature).decode("ascii")}

    def _rpc_history(self) -> Any:
        return [self._format_event(e) for e in self._vault.export_history()]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _format_key(self, key: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "did": key["did"],
            "path": key["derivation"]["path"],
            "derivation": key["derivation"],
            "extended_public_key": key["extended_public_key"],
            "extended_private_key": key["extended_private_key"],
            "public_key_b64": key["public_key_b64"],
            "secret_key_b64": key["secret_key_b64"],
            "metadata": key.get("metadata", {}),
        }

    def _format_event(self, event: VaultEvent) -> Dict[str, Any]:
        return {
            "event": event.event,
            "did": event.did,
            "path": event.path,
            "timestamp": event.timestamp,
            "metadata": dict(event.metadata),
        }

    # ------------------------------------------------------------------
    # gRPC server management
    # ------------------------------------------------------------------
    async def serve_grpc(self) -> None:
        server = grpc.aio.server()
        identity_pb2_grpc.add_IdentityLayerServicer_to_server(_GrpcIdentityServicer(self._vault), server)
        server.add_insecure_port(f"{self._config.host}:{self._config.grpc_port}")
        await server.start()
        self._grpc_server = server
        await server.wait_for_termination()

    async def shutdown_grpc(self) -> None:
        if self._grpc_server is None:
            return
        await self._grpc_server.stop(grace=None)
        self._grpc_server = None

    async def serve_all(self) -> None:
        """Start JSON-RPC and gRPC servers concurrently."""

        if uvicorn is None:  # pragma: no cover - optional dependency
            raise RuntimeError("uvicorn must be installed to run the JSON-RPC service")

        async def _serve_fastapi() -> None:
            config = uvicorn.Config(self._app, host=self._config.host, port=self._config.json_rpc_port, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()

        await asyncio.gather(_serve_fastapi(), self.serve_grpc())


class _GrpcIdentityServicer(identity_pb2_grpc.IdentityLayerServicer):
    """Adapter that bridges the vault implementation to gRPC."""

    def __init__(self, vault: EncryptedIdentityVault) -> None:
        self._vault = vault

    def _as_proto(self, key: Dict[str, Any]) -> identity_pb2.KeyRecord:
        metadata = key.get("metadata", {})
        record = identity_pb2.KeyRecord(
            did=key["did"],
            path=key["derivation"]["path"],
            extended_public_key=key["extended_public_key"],
            extended_private_key=key["extended_private_key"],
            public_key_b64=key["public_key_b64"],
            secret_key_b64=key["secret_key_b64"],
            metadata=metadata,
        )
        return record

    async def ListKeys(self, request: identity_pb2.Empty, context: grpc.aio.ServicerContext) -> identity_pb2.KeyList:  # type: ignore[override]
        keys = [self._as_proto(key) for key in self._vault.list_keys()]
        return identity_pb2.KeyList(keys=keys)

    async def EnsureKey(self, request: identity_pb2.KeyRequest, context: grpc.aio.ServicerContext) -> identity_pb2.KeyRecord:  # type: ignore[override]
        path = request.path
        key = self._vault.ensure_key(
            chain=path.chain,
            account=path.account,
            index=path.index,
            change=path.change,
            origin=request.origin,
            platform_name=request.platform or None,
        )
        return self._as_proto(key)

    async def Rotate(self, request: identity_pb2.KeyRequest, context: grpc.aio.ServicerContext) -> identity_pb2.KeyRecord:  # type: ignore[override]
        path = request.path
        key = self._vault.rotate(
            chain=path.chain,
            account=path.account,
            index=path.index,
            change=path.change,
            origin=request.origin,
        )
        return self._as_proto(key)

    async def Sign(self, request: identity_pb2.SignRequest, context: grpc.aio.ServicerContext) -> identity_pb2.SignResponse:  # type: ignore[override]
        signature = self._vault.sign(request.did, bytes(request.message))
        return identity_pb2.SignResponse(signature=signature)

    async def History(self, request: identity_pb2.Empty, context: grpc.aio.ServicerContext) -> identity_pb2.HistoryResponse:  # type: ignore[override]
        events = [
            identity_pb2.HistoryEvent(
                event=event.event,
                did=event.did,
                path=event.path,
                timestamp=event.timestamp,
                metadata=dict(event.metadata),
            )
            for event in self._vault.export_history()
        ]
        return identity_pb2.HistoryResponse(events=events)


try:  # pragma: no cover - uvicorn is optional at runtime
    import uvicorn
except ModuleNotFoundError:  # pragma: no cover
    uvicorn = None  # type: ignore[assignment]
