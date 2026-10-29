def post_review(client, menu_id, content="향이 좋아요", rating=5):
    body = {"menu_id": menu_id, "author": "민지", "content": content, "rating": rating}
    return client.post("/api/reviews", json=body)


def test_review_is_classified(client, menu):
    r = post_review(client, menu["id"])
    assert r.status_code == 201
    assert r.json()["sentiment"] == "긍정"
    assert r.json()["menu_name"] == "아메리카노"


def test_menu_aggregates(client, menu):
    post_review(client, menu["id"], "맛있어요", 5)
    post_review(client, menu["id"], "좀 별로였어요", 2)
    m = client.get(f"/api/menus/{menu['id']}").json()
    assert m["review_count"] == 2
    assert m["avg_rating"] == 3.5
    assert m["avg_sentiment"] == 0.5


def test_filter_by_sentiment(client, menu):
    post_review(client, menu["id"], "맛있어요")
    post_review(client, menu["id"], "별로")
    neg = client.get("/api/reviews", params={"sentiment": "부정"}).json()
    assert [r["content"] for r in neg] == ["별로"]


def test_stats(client, menu):
    post_review(client, menu["id"], "맛있어요", 4)
    post_review(client, menu["id"], "별로", 2)
    s = client.get("/api/stats").json()
    assert s == {"menus": 1, "reviews": 2, "avg_rating": 3.0, "positive_ratio": 0.5}


def test_review_unknown_menu(client):
    assert post_review(client, 42).status_code == 404


def test_rating_range(client, menu):
    assert post_review(client, menu["id"], rating=6).status_code == 422


def test_delete_review(client, menu):
    rid = post_review(client, menu["id"]).json()["id"]
    assert client.delete(f"/api/reviews/{rid}").status_code == 200
    assert client.delete(f"/api/reviews/{rid}").status_code == 404
