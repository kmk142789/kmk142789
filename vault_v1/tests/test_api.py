from __future__ import annotations

from fastapi.testclient import TestClient

from vault.api.main import create_app
from vault.hashing import compute_merkle_root


def test_api_ingest_retrieve_and_proof():
    client = TestClient(create_app())

    data = b"vault api data" * 100
    response = client.post(
        "/v1/files",
        files={"file": ("test.txt", data, "text/plain")},
        params={"sign": "false"},
    )
    assert response.status_code == 200
    payload = response.json()
    cid = payload["cid"]

    get_resp = client.get(f"/v1/files/{cid}")
    assert get_resp.status_code == 200
    assert get_resp.content == data

    proof_resp = client.get(f"/v1/files/{cid}/proof")
    proof = proof_resp.json()
    assert proof_resp.status_code == 200
    assert proof["cid"] == cid
    assert proof["verified"] is True
    assert proof["merkle_root"] == compute_merkle_root(proof["chunk_hashes"])
