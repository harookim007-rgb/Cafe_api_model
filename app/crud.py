import sqlite3

from .database import transaction


class NotFound(Exception):
    pass


class Duplicate(Exception):
    pass


MENU_SELECT = """
SELECT m.*,
       COUNT(r.id)                 AS review_count,
       ROUND(AVG(r.rating), 2)     AS avg_rating,
       ROUND(AVG(r.sentiment_score), 3) AS avg_sentiment
  FROM menus m
  LEFT JOIN reviews r ON r.menu_id = m.id
"""


def _menu(row):
    d = dict(row)
    d["is_soldout"] = bool(d["is_soldout"])
    return d


def list_menus(conn, category=None):
    sql = MENU_SELECT
    params = ()
    if category:
        sql += " WHERE m.category = ?"
        params = (category,)
    sql += " GROUP BY m.id ORDER BY m.id"
    return [_menu(r) for r in conn.execute(sql, params)]


def get_menu(conn, menu_id):
    row = conn.execute(MENU_SELECT + " WHERE m.id = ? GROUP BY m.id", (menu_id,)).fetchone()
    if row is None:
        raise NotFound(f"{menu_id}번 메뉴가 없습니다")
    return _menu(row)


def create_menu(conn, name, price, category):
    try:
        with transaction(conn):
            cur = conn.execute(
                "INSERT INTO menus (name, price, category) VALUES (?, ?, ?)",
                (name.strip(), price, category),
            )
    except sqlite3.IntegrityError:
        raise Duplicate(f"'{name}' 메뉴가 이미 있습니다")
    return get_menu(conn, cur.lastrowid)


UPDATABLE = ("name", "price", "category", "is_soldout")


def update_menu(conn, menu_id, data):
    get_menu(conn, menu_id)
    fields = {k: v for k, v in data.items() if k in UPDATABLE and v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        try:
            with transaction(conn):
                conn.execute(f"UPDATE menus SET {sets} WHERE id = ?", (*fields.values(), menu_id))
        except sqlite3.IntegrityError:
            raise Duplicate("같은 이름의 메뉴가 이미 있습니다")
    return get_menu(conn, menu_id)


def delete_menu(conn, menu_id):
    menu = get_menu(conn, menu_id)
    with transaction(conn):
        conn.execute("DELETE FROM menus WHERE id = ?", (menu_id,))
    return menu


REVIEW_SELECT = """
SELECT r.*, m.name AS menu_name
  FROM reviews r
  JOIN menus m ON m.id = r.menu_id
"""


def create_review(conn, menu_id, author, content, rating, sentiment=None, score=None):
    get_menu(conn, menu_id)
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO reviews (menu_id, author, content, rating, sentiment, sentiment_score) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (menu_id, author.strip(), content.strip(), rating, sentiment, score),
        )
    return dict(conn.execute(REVIEW_SELECT + " WHERE r.id = ?", (cur.lastrowid,)).fetchone())


def list_reviews(conn, menu_id=None, sentiment=None, limit=20):
    sql, params, where = REVIEW_SELECT, [], []
    if menu_id:
        where.append("r.menu_id = ?")
        params.append(menu_id)
    if sentiment:
        where.append("r.sentiment = ?")
        params.append(sentiment)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.id DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(sql, params)]


def delete_review(conn, review_id):
    row = conn.execute(REVIEW_SELECT + " WHERE r.id = ?", (review_id,)).fetchone()
    if row is None:
        raise NotFound(f"{review_id}번 리뷰가 없습니다")
    with transaction(conn):
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    return dict(row)


def stats(conn):
    menus = conn.execute("SELECT COUNT(*) FROM menus").fetchone()[0]
    r = conn.execute(
        "SELECT COUNT(*), AVG(rating), AVG(CASE WHEN sentiment = '긍정' THEN 1.0 ELSE 0 END) "
        "FROM reviews"
    ).fetchone()
    count, avg_rating, pos = r
    return {
        "menus": menus,
        "reviews": count,
        "avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
        "positive_ratio": round(pos, 3) if count else None,
    }
