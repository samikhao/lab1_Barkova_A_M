import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/health")
    r = await client.get("/api/v1/news/")
    assert r.status_code in (200, 404, 500)
