from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.api.routes_cap import CapState, Capability, router as cap_router
from echo.api.routes_receipts import router as receipts_router
from echo.receipts import default_key, make_receipt


def test_capability_plan_endpoint(monkeypatch):
    app = FastAPI()
    app.include_router(cap_router)
    client = TestClient(app)

    catalog = {
        "net.init": Capability("net.init"),
        "auth.keyring": Capability("auth.keyring"),
        "bridge.firebase.deploy": Capability(
            "bridge.firebase.deploy", requires={"net.init", "auth.keyring"}
        ),
    }

    monkeypatch.setattr("echo.api.routes_cap.load_catalog", lambda: catalog)
    monkeypatch.setattr(
        "echo.api.routes_cap.load_state", lambda: CapState(provided={"net.init"})
    )

    response = client.post("/api/cap/plan", json={"name": "bridge.firebase.deploy"})
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "count": 2,
        "steps": ["auth.keyring", "bridge.firebase.deploy"],
    }


def test_receipt_verify_endpoint():
    app = FastAPI()
    app.include_router(receipts_router)
    client = TestClient(app)

    key = default_key()
    receipt = make_receipt("run", {"x": 1}, "0x00", key)

    response = client.post("/api/receipts/verify", json=receipt.to_dict())
    assert response.status_code == 200
    assert response.json() == {"valid": True}
