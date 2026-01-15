import pytest


@pytest.mark.asyncio
async def test_news_create_requires_verified_author(client, normal_user, token_factory):
    token = token_factory(normal_user)
    r = await client.post(
        "/api/v1/news/",
        json={"title": "X", "content": {"a": 1}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] in (
        "Author verification required",
        "author is not verified to publish news",
    )


@pytest.mark.asyncio
async def test_news_crud_and_cache(client, verified_author, token_factory):
    token = token_factory(verified_author)
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/news/",
        json={"title": "Hello", "content": {"text": "world"}, "cover_url": None},
        headers=headers,
    )
    assert r.status_code == 201
    news = r.json()
    nid = news["id"]
    assert news["author_id"] == verified_author.id

    r1 = await client.get("/api/v1/news/")
    assert r1.status_code == 200
    assert any(x["id"] == nid for x in r1.json())

    r2 = await client.get("/api/v1/news/")
    assert r2.status_code == 200
    assert any(x["id"] == nid for x in r2.json())

    r = await client.patch(
        f"/api/v1/news/{nid}",
        json={"title": "Hello2"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Hello2"

    r = await client.delete(f"/api/v1/news/{nid}", headers=headers)
    assert r.status_code == 204

    r = await client.delete(f"/api/v1/news/{nid}", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_news_update_forbidden_for_non_owner(
    client, verified_author, normal_user, token_factory
):
    token_a = token_factory(verified_author)
    r = await client.post(
        "/api/v1/news/",
        json={"title": "Owned", "content": None},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201
    nid = r.json()["id"]

    token_u = token_factory(normal_user)
    r = await client.patch(
        f"/api/v1/news/{nid}",
        json={"title": "Hack"},
        headers={"Authorization": f"Bearer {token_u}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_news_update_allowed_for_admin(
    client, verified_author, admin_user, token_factory
):
    token_a = token_factory(verified_author)
    r = await client.post(
        "/api/v1/news/",
        json={"title": "Admin can edit", "content": None},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201
    nid = r.json()["id"]

    token_admin = token_factory(admin_user)
    r = await client.patch(
        f"/api/v1/news/{nid}",
        json={"title": "Edited by admin"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Edited by admin"
