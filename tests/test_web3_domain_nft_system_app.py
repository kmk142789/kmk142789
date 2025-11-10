from __future__ import annotations

import pytest

from web3_domain_nft_system import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(database_path=tmp_path / "app.db")
    app.config.update(TESTING=True)
    return app.test_client()


def test_crypto_health_endpoint(client):
    response = client.get("/api/crypto/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "Web3 Domain NFT Generator"


def test_user_crud_cycle(client):
    create_response = client.post(
        "/api/users",
        json={"username": "alice", "email": "alice@example.com"},
    )
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert created["username"] == "alice"

    list_response = client.get("/api/users")
    assert list_response.status_code == 200
    users = list_response.get_json()
    assert any(user["email"] == "alice@example.com" for user in users)


def test_nft_routes_exposed(client):
    mint_response = client.post(
        "/api/nft/mint",
        json={
            "domain_name": "example.eth",
            "owner_address": "0x" + "a" * 40,
            "metadata": {"name": "Example"},
        },
    )
    assert mint_response.status_code == 201

    info_response = client.get("/api/nft/info/example.eth")
    assert info_response.status_code == 200
    data = info_response.get_json()
    assert data["found"] is True
    assert data["data"]["domain_name"] == "example.eth"


def test_static_index_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Web3 Domain NFT System" in response.data
