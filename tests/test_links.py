def test_create_link_requires_auth(client):
    resp = client.post("/links", json={"target_url": "https://example.com"})
    assert resp.status_code == 401


def test_create_link_success(client, auth_headers):
    resp = client.post(
        "/links",
        json={"target_url": "https://example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_url"].startswith("https://example.com")
    assert len(data["short_code"]) > 0
    assert data["click_count"] == 0


def test_create_link_invalid_url(client, auth_headers):
    resp = client.post(
        "/links",
        json={"target_url": "not-a-url"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_redirect_increments_counter(client, auth_headers):
    create = client.post(
        "/links",
        json={"target_url": "https://example.com"},
        headers=auth_headers,
    )
    code = create.json()["short_code"]

    resp = client.get(f"/r/{code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"].startswith("https://example.com")

    link_id = create.json()["id"]
    stats = client.get(f"/links/{link_id}/stats", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["click_count"] == 1


def test_redirect_unknown_code_returns_404(client):
    resp = client.get("/r/doesnotexist", follow_redirects=False)
    assert resp.status_code == 404


def test_favicon_not_routed_to_redirect(client):
    resp = client.get("/favicon.ico", follow_redirects=False)
    assert resp.status_code == 404


def test_list_returns_only_own_links(client):
    # User A creates a link
    client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "password123"},
    )
    token_a = client.post(
        "/auth/login",
        data={"username": "a@example.com", "password": "password123"},
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    client.post(
        "/links",
        json={"target_url": "https://a.com"},
        headers=headers_a,
    )

    # User B sees no links
    client.post(
        "/auth/register",
        json={"email": "b@example.com", "password": "password123"},
    )
    token_b = client.post(
        "/auth/login",
        data={"username": "b@example.com", "password": "password123"},
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = client.get("/links", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []


def test_cannot_access_other_users_link_stats(client):
    # User A creates a link
    client.post(
        "/auth/register",
        json={"email": "a2@example.com", "password": "password123"},
    )
    token_a = client.post(
        "/auth/login",
        data={"username": "a2@example.com", "password": "password123"},
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    link = client.post(
        "/links",
        json={"target_url": "https://a.com"},
        headers=headers_a,
    ).json()

    # User B tries to access
    client.post(
        "/auth/register",
        json={"email": "b2@example.com", "password": "password123"},
    )
    token_b = client.post(
        "/auth/login",
        data={"username": "b2@example.com", "password": "password123"},
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = client.get(f"/links/{link['id']}/stats", headers=headers_b)
    assert resp.status_code == 404


def test_delete_link(client, auth_headers):
    create = client.post(
        "/links",
        json={"target_url": "https://example.com"},
        headers=auth_headers,
    )
    link_id = create.json()["id"]

    resp = client.delete(f"/links/{link_id}", headers=auth_headers)
    assert resp.status_code == 204

    stats = client.get(f"/links/{link_id}/stats", headers=auth_headers)
    assert stats.status_code == 404


def test_delete_nonexistent_link(client, auth_headers):
    resp = client.delete("/links/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_invalid_jwt_rejected(client):
    headers = {"Authorization": "Bearer totally-invalid-token"}
    resp = client.get("/links", headers=headers)
    assert resp.status_code == 401
