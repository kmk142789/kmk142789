"""FastAPI router for Echo Atlas."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from .domain import Edge, EntityType, Node, RelationType
from .schema import validate_graph, ValidationError
from .service import AtlasService


def create_router(service: AtlasService) -> APIRouter:
    router = APIRouter(prefix="/atlas", tags=["atlas"])

    @router.get("/nodes")
    def get_nodes():
        return [node.as_dict() for node in service.list_nodes()]

    @router.get("/edges")
    def get_edges():
        return [edge.as_dict() for edge in service.list_edges()]

    @router.get("/summary")
    def get_summary():
        return service.build_summary().as_dict()

    @router.post("/hooks", status_code=202)
    async def ingest_hook(request: Request):
        signature = request.headers.get("X-Atlas-Signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature header")
        payload = await request.json()
        # Signature verification stub
        if not isinstance(signature, str):
            raise HTTPException(status_code=400, detail="Invalid signature header")
        nodes_payload = payload.get("nodes", [])
        edges_payload = payload.get("edges", [])
        if not isinstance(nodes_payload, list) or not isinstance(edges_payload, list):
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        try:
            validate_graph(
                {
                    "generated_at": payload.get("generated_at", "1970-01-01T00:00:00Z"),
                    "nodes": nodes_payload,
                    "edges": edges_payload,
                    "change_log": payload.get("change_log", []),
                }
            )
        except ValidationError:
            pass
        for item in nodes_payload:
            try:
                node = Node(
                    identifier=item["id"],
                    name=item.get("name", item["id"]),
                    entity_type=EntityType(item.get("entity_type", "Service")),
                    metadata=item.get("metadata", {}),
                )
            except KeyError as exc:  # pragma: no cover - defensive
                raise HTTPException(status_code=400, detail=f"Missing node field: {exc}") from exc
            service.repository.upsert_node(node)
        for item in edges_payload:
            try:
                edge = Edge(
                    identifier=item["id"],
                    source=item["source"],
                    target=item["target"],
                    relation=RelationType(item.get("relation", "CONNECTS_TO")),
                    metadata=item.get("metadata", {}),
                )
            except KeyError as exc:  # pragma: no cover - defensive
                raise HTTPException(status_code=400, detail=f"Missing edge field: {exc}") from exc
            service.repository.upsert_edge(edge)
        service.append_highlight("Webhook update received")
        return {"status": "accepted"}

    @router.get("", response_class=HTMLResponse)
    def atlas_view() -> str:
        nodes = service.list_nodes()
        edges = service.list_edges()
        svg = service.project_root.joinpath("artifacts", "atlas_graph.svg")
        svg_html = svg.read_text(encoding="utf-8") if svg.exists() else "<p>No graph yet.</p>"
        return (
            "<html><head><title>Echo Atlas</title></head><body>"
            "<h1>Echo Atlas Viewer</h1>"
            f"<pre>{service.build_summary().as_dict()}</pre>"
            f"<div>{svg_html}</div>"
            "</body></html>"
        )

    return router


def create_app(service: AtlasService) -> FastAPI:
    app = FastAPI(title="Echo Atlas", version="1.0.0")
    app.include_router(create_router(service))
    return app
