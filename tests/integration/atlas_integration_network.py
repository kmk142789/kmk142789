from atlas.network import NodeInfo, NodeRegistry, Pathfinder, RoutingTable


def test_pathfinder():
    registry = NodeRegistry()
    registry.register(NodeInfo(id="A", host="localhost", port=8001))
    registry.register(NodeInfo(id="B", host="localhost", port=8002))
    registry.register(NodeInfo(id="C", host="localhost", port=8003))

    routing = RoutingTable()
    routing.update(registry.get("A"), registry.get("B"), 0.9)  # type: ignore[arg-type]
    routing.update(registry.get("B"), registry.get("C"), 0.9)  # type: ignore[arg-type]

    pathfinder = Pathfinder(registry, routing)
    path = pathfinder.best_path("A", "C")
    assert path == ["A", "B", "C"]
