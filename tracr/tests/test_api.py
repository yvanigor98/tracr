import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "tracr"


@pytest.mark.asyncio
async def test_create_source(client):
    response = await client.post("/sources/", json={
        "name": "Test RSS Feed",
        "type": "rss",
        "url": "https://example.com/feed.xml",
        "active": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test RSS Feed"
    assert data["type"] == "rss"
    assert data["active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sources(client):
    # Create a source first
    await client.post("/sources/", json={
        "name": "List Test Feed",
        "type": "rss",
        "url": "https://example.com/list-test.xml",
        "active": True,
    })
    response = await client.get("/sources/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_source_not_found(client):
    response = await client.get("/sources/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_entities_empty(client):
    response = await client.get("/entities/search")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_entity_not_found(client):
    response = await client.get("/entities/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
