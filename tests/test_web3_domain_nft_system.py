import pytest

from apps.web3_domain_nft_system import NFTMinter, create_app


@pytest.fixture()
def minter() -> NFTMinter:
    return NFTMinter()


@pytest.fixture()
def client(minter: NFTMinter):
    app = create_app(minter)
    app.config.update(TESTING=True)
    return app.test_client()


def _payload(domain: str, *, owner: str = "0x" + "a" * 40, metadata=None):
    metadata = metadata or {"name": domain}
    return {"domain_name": domain, "owner_address": owner, "metadata": metadata}


def test_mint_domain_success(client):
    response = client.post("/mint", json=_payload("example.eth"))
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["message"] == "NFT minted successfully"
    data = payload["data"]
    assert data["domain_name"] == "example.eth"
    assert data["owner_address"].lower() == ("0x" + "a" * 40)
    assert data["status"] == "confirmed"


def test_mint_domain_rejects_duplicate(client):
    assert client.post("/mint", json=_payload("duplicate.eth")).status_code == 201
    response = client.post("/mint", json=_payload("duplicate.eth"))
    assert response.status_code == 409
    assert "Domain name already exists" in response.get_json()["message"]


def test_check_availability(client):
    response = client.post("/check-availability", json={"domain_name": "fresh.eth"})
    assert response.status_code == 200
    assert response.get_json()["available"] is True

    client.post("/mint", json=_payload("fresh.eth"))
    response = client.post("/check-availability", json={"domain_name": "fresh.eth"})
    assert response.get_json()["available"] is False


def test_info_endpoint_returns_data(client):
    client.post("/mint", json=_payload("lookup.eth"))
    response = client.get("/info/lookup.eth")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["found"] is True
    assert payload["data"]["domain_name"] == "lookup.eth"


def test_batch_mint_reports_failures(client):
    success = _payload("success.eth")
    missing_owner = {"domain_name": "broken.eth", "metadata": {}}
    response = client.post("/batch-mint", json={"domains": [success, missing_owner]})
    assert response.status_code == 200
    data = response.get_json()
    assert data["successful_mints"] == 1
    assert data["failed_mints"] == 1
    failure = next(item for item in data["results"] if item["domain_name"] == "broken.eth")
    assert failure["success"] is False


def test_stats_endpoint(client):
    client.post("/mint", json=_payload("stats-one.eth"))
    client.post("/mint", json=_payload("stats-two.eth", owner="0x" + "b" * 40))
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.get_json()["data"]
    assert stats["total_domains_minted"] == 2
    assert stats["unique_owners"] == 2
    assert stats["total_gas_used"] > 0
