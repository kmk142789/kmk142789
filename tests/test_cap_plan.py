from echo.cap.model import Capability, CapState
from echo.cap.plan import plan_install


def test_plan_orders_dependencies():
    catalog = {
        "A": Capability("A", requires={"B", "C"}),
        "B": Capability("B"),
        "C": Capability("C", requires={"D"}),
        "D": Capability("D"),
    }
    plan = plan_install(catalog["A"], catalog, CapState())
    assert [c.name for c in plan] == ["D", "C", "B", "A"]
