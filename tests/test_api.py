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


async def test_price_statistics(client: AsyncClient):
    """
    Test that /prices/stats returns aggregated statistics.
    """
    response = await client.get("/prices/stats?days=7")

    assert response.status_code == 200
    data = response.json()

    assert "period" in data
    assert "avg_price" in data
    assert "max_price" in data
    assert "min_price" in data
    assert "peak_hour" in data
    assert "cheapest_hour" in data

    if data["avg_price"] is not None:
        assert isinstance(data["avg_price"], (int, float))
        assert isinstance(data["max_price"], (int, float))
        assert isinstance(data["min_price"], (int, float))

        if data["peak_hour"] is not None:
            assert 0 <= data["peak_hour"] <= 23
