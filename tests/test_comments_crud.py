import pytest


@pytest.mark.asyncio
async def test_comment_crud_and_permissions(
    client, verified_author, normal_user, token_factory
):
    t_author = token_factory(verified_author)
    r = await client.post(
        "/api/v1/news/",
        json={"title": "Post", "content": None},
        headers={"Authorization": f"Bearer {t_author}"},
    )
    assert r.status_code == 201
    nid = r.json()["id"]

    t_user = token_factory(normal_user)
    r = await client.post(
        "/api/v1/comments/",
        json={"text": "hi", "news_id": nid},
        headers={"Authorization": f"Bearer {t_user}"},
    )
    assert r.status_code == 201
    cid = r.json()["id"]
    assert r.json()["author_id"] == normal_user.id

    r = await client.get("/api/v1/comments/")
    assert r.status_code == 200
    assert any(x["id"] == cid for x in r.json())

    r = await client.patch(
        f"/api/v1/comments/{cid}",
        json={"text": "nope"},
        headers={"Authorization": f"Bearer {t_author}"},
    )
    assert r.status_code == 403

    r = await client.patch(
        f"/api/v1/comments/{cid}",
        json={"text": "edited"},
        headers={"Authorization": f"Bearer {t_user}"},
    )
    assert r.status_code == 200
    assert r.json()["text"] == "edited"

    r = await client.delete(
        f"/api/v1/comments/{cid}",
        headers={"Authorization": f"Bearer {t_user}"},
    )
    assert r.status_code == 204

    r = await client.delete(
        f"/api/v1/comments/{cid}",
        headers={"Authorization": f"Bearer {t_user}"},
    )
    assert r.status_code in (204, 404)


@pytest.mark.asyncio
async def test_comment_create_news_not_found(client, normal_user, token_factory):
    t = token_factory(normal_user)
    r = await client.post(
        "/api/v1/comments/",
        json={"text": "x", "news_id": 999999},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "news not found"
