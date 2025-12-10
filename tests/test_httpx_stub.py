import pytest

import httpx


def test_client_can_return_mock_response():
    response = httpx.Response(status_code=200, _json={"ok": True}, _text="ok")
    client = httpx.Client(mock_responses={"https://example.test": response})

    result = client.post("https://example.test")

    assert result is response
    assert result.json() == {"ok": True}
    assert result.is_success


def test_raise_for_status_uses_http_status_error():
    response = httpx.Response(status_code=503, _json={}, _text="")

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        response.raise_for_status()

    assert excinfo.value.status_code == 503
    assert excinfo.value.response is response


@pytest.mark.asyncio
async def test_async_client_get_uses_mock_response():
    response = httpx.Response(status_code=200, _json={"hello": "world"}, _text="ok")

    async with httpx.AsyncClient(mock_responses={"https://example.test": response}) as client:
        result = await client.get("https://example.test")

    assert result is response
    assert result.json()["hello"] == "world"
