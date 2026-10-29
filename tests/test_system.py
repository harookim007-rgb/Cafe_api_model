def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_ready(client):
    r = client.get("/ready").json()
    assert r["status"] == "ok"
    assert all(r["checks"].values())


def test_request_id(client):
    r = client.get("/health", headers={"x-request-id": "abc"})
    assert r.headers["x-request-id"] == "abc"


def test_admin_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Cafe AI" in r.text
    assert client.get("/js/app.js").status_code == 200


def test_seed_demo(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings(db_path=str(tmp_path / "demo.db"), seed_demo=True))
    with TestClient(app) as c:
        assert len(c.get("/api/menus").json()) == 8
        assert c.get("/api/stats").json()["reviews"] == 5
