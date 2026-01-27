import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


async def test_get_prices_structure(client: AsyncClient):
    limit = 3
    response = await client.get(f"/prices?limit={limit}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        assert len(data) <= limit
        first_item = data[0]
        assert "timestamp" in first_item
        assert "price" in first_item
        assert "zone_id" in first_item
        assert isinstance(first_item["price"], (int, float))


async def test_get_prices_pagination(client: AsyncClient):
    response = await client.get("/prices?limit=1")
    assert response.status_code == 200
    assert len(response.json()) <= 1
