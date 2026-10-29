def test_create_menu(client):
    r = client.post("/api/menus", json={"name": "라떼", "price": 5000, "category": "커피"})
    assert r.status_code == 201
    assert r.json()["is_soldout"] is False


def test_list_by_category(client, menu):
    client.post("/api/menus", json={"name": "치즈케이크", "price": 6500, "category": "디저트"})
    names = [m["name"] for m in client.get("/api/menus", params={"category": "디저트"}).json()]
    assert names == ["치즈케이크"]


def test_invalid_input(client):
    assert client.post("/api/menus", json={"name": "", "price": 4500}).status_code == 422
    assert client.post("/api/menus", json={"name": "물", "price": 0}).status_code == 422
    assert client.post("/api/menus", json={"name": "물", "price": 1000, "category": "주류"}).status_code == 422


def test_duplicate_name(client, menu):
    r = client.post("/api/menus", json={"name": "아메리카노", "price": 3000})
    assert r.status_code == 409


def test_patch_price_and_soldout(client, menu):
    r = client.patch(f"/api/menus/{menu['id']}", json={"price": 4800, "is_soldout": True})
    assert r.json()["price"] == 4800
    assert r.json()["is_soldout"] is True


def test_not_found(client):
    assert client.get("/api/menus/999").status_code == 404
    assert client.patch("/api/menus/999", json={"price": 1000}).status_code == 404


def test_delete_menu_removes_reviews(client, menu):
    client.post("/api/reviews", json={"menu_id": menu["id"], "author": "a", "content": "맛있어요", "rating": 5})
    assert client.delete(f"/api/menus/{menu['id']}").status_code == 200
    assert client.get("/api/reviews").json() == []


def test_sql_injection(client, menu):
    r = client.get("/api/menus", params={"category": "커피' OR '1'='1"})
    assert r.status_code == 422
    assert len(client.get("/api/menus").json()) == 1
