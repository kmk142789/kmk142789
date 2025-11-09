"""Lightweight FastAPI shim used in the kata test-suite.

This module provides a tiny subset of the `fastapi` API so that the project can
run inside the execution environment without pulling in the real dependency.  It
supports the features exercised by the tests: route registration via
:class:`FastAPI`/:class:`APIRouter`, dependency injection with :func:`Depends`,
HTTP and WebSocket handlers, and a synchronous :class:`TestClient` capable of
calling them without spinning up an ASGI server.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import threading
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, Optional, get_type_hints

__all__ = [
    "APIRouter",
    "Depends",
    "FastAPI",
    "HTTPException",
    "Query",
    "Request",
    "Response",
    "WebSocket",
    "WebSocketDisconnect",
    "status",
]


class HTTPException(Exception):
    """Simple HTTP error with a status code and optional detail."""

    def __init__(self, *, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Response:
    """Basic response container mirroring FastAPI's object."""

    def __init__(
        self,
        *,
        content: Any = None,
        status_code: int = 200,
        media_type: str = "application/json",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.media_type = media_type
        self.headers = dict(headers or {})


class _Dependency:
    def __init__(self, provider: Callable[[], Any]) -> None:
        self.provider = provider

    def resolve(self) -> Any:
        return self.provider()


def Depends(provider: Callable[[], Any]) -> Any:
    return _Dependency(provider)


class Request:
    """Minimal request object passed to handlers."""

    def __init__(
        self,
        *,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        json_body: Any = None,
    ) -> None:
        self.method = method.upper()
        self.url = path
        self.headers = dict(headers or {})
        self.query_params = dict(query_params or {})
        self._json_body = json_body

    async def json(self) -> Any:
        return self._json_body


class Query:
    """Descriptor used to declare query parameters with defaults."""

    def __init__(self, default: Any = None, **_constraints: Any) -> None:
        self.default = default

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Query(default={self.default!r})"


class WebSocketDisconnect(Exception):
    """Raised when the WebSocket connection is terminated."""


class WebSocket:
    """Server-side WebSocket object consumed by handlers."""

    def __init__(self, connection: "_WebSocketConnection") -> None:
        self._connection = connection
        self.headers: Dict[str, str] = {}
        self.client = SimpleNamespace(host="testclient", port=0)
        self._accepted = False

    async def accept(self) -> None:
        self._accepted = True

    async def close(self) -> None:  # pragma: no cover - symmetry helper
        await self._connection._close_server()

    async def send_json(self, payload: Any) -> None:
        if not self._accepted:
            await self.accept()
        await self._connection._queue_to_client(payload)

    async def receive_json(self) -> Any:
        return await self._connection._queue_from_client()


@dataclass
class _Route:
    path: str
    method: str
    endpoint: Callable[..., Any]
    status_code: Optional[int] = None
    response_class: Optional[type[Response]] = None
    response_model: Any | None = None

    def copy_with(self, *, path: str, prefix: str = "") -> "_Route":
        new_path = _join_paths(prefix, path)
        return _Route(
            path=new_path,
            method=self.method,
            endpoint=self.endpoint,
            status_code=self.status_code,
            response_class=self.response_class,
            response_model=self.response_model,
        )


def _join_paths(*parts: str) -> str:
    segments: list[str] = []
    for part in parts:
        if not part:
            continue
        segment = part.strip()
        if not segment:
            continue
        if segment == "/":
            segments.append("")
            continue
        segment = segment.strip("/")
        if segment:
            segments.append(segment)
    return "/" + "/".join(segments)


class APIRouter:
    """Collect routes before they are attached to an application."""

    def __init__(self, *, prefix: str = "", tags: Optional[Iterable[str]] = None) -> None:
        self.prefix = prefix
        self.tags = list(tags or [])
        self.routes: list[_Route] = []

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Iterable[str],
        status_code: Optional[int] = None,
        response_class: Optional[type[Response]] = None,
        response_model: Any | None = None,
        **_extra: Any,
    ) -> None:
        for method in methods:
            self.routes.append(
                _Route(
                    path=_join_paths(self.prefix, path),
                    method=method.upper(),
                    endpoint=endpoint,
                    status_code=status_code,
                    response_class=response_class,
                    response_model=response_model,
                )
            )

    def _decorate(
        self,
        path: str,
        *,
        methods: Iterable[str],
        status_code: Optional[int] = None,
        response_class: Optional[type[Response]] = None,
        response_model: Any | None = None,
        **_extra: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(
                path,
                func,
                methods=methods,
                status_code=status_code,
                response_class=response_class,
                response_model=response_model,
                **_extra,
            )
            return func

        return decorator

    def get(
        self,
        path: str,
        *,
        status_code: Optional[int] = None,
        response_class: Optional[type[Response]] = None,
        response_model: Any | None = None,
        **extra: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorate(
            path,
            methods=["GET"],
            status_code=status_code,
            response_class=response_class,
            response_model=response_model,
            **extra,
        )

    def post(
        self,
        path: str,
        *,
        status_code: Optional[int] = None,
        response_class: Optional[type[Response]] = None,
        response_model: Any | None = None,
        **extra: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorate(
            path,
            methods=["POST"],
            status_code=status_code,
            response_class=response_class,
            response_model=response_model,
            **extra,
        )

    def websocket(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorate(path, methods=["WEBSOCKET"])


class FastAPI(APIRouter):
    """Simplified application object that reuses :class:`APIRouter`."""

    def __init__(self, *, title: str | None = None, version: str | None = None) -> None:
        super().__init__()
        self.title = title or "FastAPI"
        self.version = version or "0"

    def include_router(self, router: APIRouter, *, prefix: str = "") -> None:
        for route in router.routes:
            self.routes.append(route.copy_with(path=route.path, prefix=prefix))

    def _find_route(self, method: str, path: str) -> _Route:
        for route in self.routes:
            if route.method == method and route.path == path:
                return route
        raise LookupError(f"No route registered for {method} {path}")

    async def _execute(
        self,
        route: _Route,
        *,
        request: Request,
        body: Any,
        query: Dict[str, str],
    ) -> tuple[Any, int, Dict[str, str], str]:
        kwargs = _build_call_kwargs(route.endpoint, request=request, body=body, query=query)
        try:
            result = route.endpoint(**kwargs)
            if inspect.iscoroutine(result):
                result = await result
        except HTTPException as exc:
            payload: Any = {"detail": exc.detail} if exc.detail is not None else None
            return payload, exc.status_code, {}, "application/json"
        if isinstance(result, Response):
            status = result.status_code or route.status_code or 200
            media_type = result.media_type
            payload = result.content
            headers = dict(result.headers)
        else:
            status = route.status_code or 200
            payload = result
            media_type = "application/json"
            headers: Dict[str, str] = {}
            response_cls = route.response_class
            if response_cls and issubclass(response_cls, Response):
                response_obj = response_cls(content=result, status_code=status)
                media_type = response_obj.media_type
                headers = dict(response_obj.headers)
                payload = response_obj.content
        return payload, status, headers, media_type

    async def _run_websocket(self, route: _Route, websocket: WebSocket) -> None:
        result = route.endpoint(websocket)
        if inspect.iscoroutine(result):
            await result


def _build_call_kwargs(
    endpoint: Callable[..., Any],
    *,
    request: Request,
    body: Any,
    query: Dict[str, str],
) -> Dict[str, Any]:
    signature = inspect.signature(endpoint)
    kwargs: Dict[str, Any] = {}
    type_hints = get_type_hints(endpoint)
    body_params = [
        name
        for name, param in signature.parameters.items()
        if _is_body_parameter(param)
    ]
    for name, param in signature.parameters.items():
        annotation = type_hints.get(name, param.annotation)
        default = param.default
        if isinstance(default, _Dependency):
            kwargs[name] = default.resolve()
            continue
        if annotation is Request:
            kwargs[name] = request
            continue
        if name in query:
            kwargs[name] = _convert_value(query[name], annotation)
            continue
        if name in body_params:
            kwargs[name] = _build_body_argument(name, annotation, body, body_params)
            continue
        if default is not inspect._empty:
            if isinstance(default, Query):
                kwargs[name] = default.default
            else:
                kwargs[name] = default
    return kwargs


def _is_body_parameter(param: inspect.Parameter) -> bool:
    if isinstance(param.default, _Dependency):
        return False
    if param.annotation is Request:
        return False
    return param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)


def _build_body_argument(
    name: str,
    annotation: Any,
    body: Any,
    body_params: list[str],
) -> Any:
    if body is None:
        data = None
    elif isinstance(body, dict) and len(body_params) > 1:
        data = body.get(name)
    elif isinstance(body, dict) and name in body:
        data = body[name]
    else:
        data = body
    if annotation is inspect._empty or data is None:
        return data
    converter = getattr(annotation, "model_validate", None)
    if callable(converter):
        return converter(data)
    try:
        return annotation(data)
    except Exception:
        return data


def _convert_value(value: str, annotation: Any) -> Any:
    if annotation in (inspect._empty, str) or value is None:
        return value
    try:
        if annotation is int:
            return int(value)
        if annotation is float:
            return float(value)
        if annotation is bool:
            return value.lower() not in {"0", "false", "no"}
    except Exception:
        return value
    return annotation(value) if callable(annotation) else value


class status:
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_400_BAD_REQUEST = 400
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_429_TOO_MANY_REQUESTS = 429
    HTTP_503_SERVICE_UNAVAILABLE = 503


class _ClientResponse:
    def __init__(
        self,
        *,
        payload: Any,
        status_code: int,
        media_type: str,
        headers: Dict[str, str],
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.media_type = media_type
        if isinstance(payload, (dict, list)):
            self._json_payload = payload
            self._text = json.dumps(payload)
            self._content = self._text.encode("utf-8")
        elif hasattr(payload, "model_dump"):
            data = payload.model_dump()
            self._json_payload = data
            self._text = json.dumps(data)
            self._content = self._text.encode("utf-8")
        elif isinstance(payload, bytes):
            self._json_payload = None
            self._content = payload
            self._text = payload.decode("utf-8", errors="replace")
        elif payload is None:
            self._json_payload = None
            self._content = b""
            self._text = ""
        else:
            text = str(payload)
            self._json_payload = None
            self._text = text
            self._content = text.encode("utf-8")

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._content

    def json(self) -> Any:
        if self._json_payload is not None:
            return self._json_payload
        if not self._text:
            raise ValueError("response does not contain JSON content")
        return json.loads(self._text)


class TestClient:
    """Execute handlers registered on a :class:`FastAPI` instance."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> _ClientResponse:
        method = method.upper()
        query: Dict[str, str] = {}
        if params:
            query.update({k: str(v) for k, v in params.items()})
        if "?" in path:
            path, query_string = path.split("?", 1)
            for part in query_string.split("&"):
                if not part:
                    continue
                if "=" in part:
                    key, value = part.split("=", 1)
                    query.setdefault(key, value)
                else:
                    query.setdefault(part, "")
        route = self.app._find_route(method, path)
        request = Request(method=method, path=path, headers=headers, query_params=query, json_body=json)
        payload, status_code, response_headers, media_type = asyncio.run(
            self.app._execute(route, request=request, body=json, query=query)
        )
        return _ClientResponse(
            payload=payload,
            status_code=status_code,
            media_type=media_type,
            headers=response_headers,
        )

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> _ClientResponse:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json: Any | None = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> _ClientResponse:
        return self.request("POST", path, json=json, headers=headers)

    def websocket_connect(self, path: str) -> "_WebSocketConnection":
        route = self.app._find_route("WEBSOCKET", path)
        return _WebSocketConnection(self.app, route)


TestClient.__test__ = False  # Prevent pytest from treating the class as a test case.


class _WebSocketConnection:
    """Context manager bridging async WebSocket handlers with tests."""

    def __init__(self, app: FastAPI, route: _Route) -> None:
        self._app = app
        self._route = route
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._ready = threading.Event()
        self._closed = False
        self._server_task: asyncio.Task[Any] | None = None
        self._to_client: asyncio.Queue[Any] | None = None
        self._from_client: asyncio.Queue[Any] | None = None

    def __enter__(self) -> "_WebSocketConnection":
        self._thread.start()
        self._ready.wait()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._server_task:
            asyncio.run_coroutine_threadsafe(self._cancel_server(), self._loop).result()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()

    async def _cancel_server(self) -> None:
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            with contextlib.suppress(Exception):
                await self._server_task

    def receive_json(self) -> Any:
        if not self._to_client:
            raise RuntimeError("websocket not initialised")
        future = asyncio.run_coroutine_threadsafe(self._to_client.get(), self._loop)
        return future.result()

    def send_json(self, payload: Any) -> None:
        if not self._from_client:
            raise RuntimeError("websocket not initialised")
        asyncio.run_coroutine_threadsafe(self._from_client.put(payload), self._loop).result()

    async def _queue_to_client(self, payload: Any) -> None:
        if self._to_client:
            await self._to_client.put(payload)

    async def _queue_from_client(self) -> Any:
        if not self._from_client:
            raise WebSocketDisconnect()
        return await self._from_client.get()

    async def _close_server(self) -> None:
        raise WebSocketDisconnect()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._to_client = asyncio.Queue()
        self._from_client = asyncio.Queue()
        websocket = WebSocket(self)
        self._server_task = self._loop.create_task(self._app._run_websocket(self._route, websocket))
        self._ready.set()
        try:
            self._loop.run_forever()
        finally:
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()
            with contextlib.suppress(Exception):
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._loop.close()


# ``fastapi.testclient`` re-exports :class:`TestClient` for compatibility.
from . import testclient  # noqa: E402  # type: ignore
