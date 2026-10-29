from . import crud

MENUS = [
    ("아메리카노", 4500, "커피"),
    ("카페라떼", 5000, "커피"),
    ("바닐라라떼", 5500, "커피"),
    ("콜드브루", 5000, "커피"),
    ("말차라떼", 5800, "논커피"),
    ("자몽에이드", 6000, "논커피"),
    ("얼그레이", 4800, "티"),
    ("바스크 치즈케이크", 6500, "디저트"),
]

REVIEWS = [
    (1, "민지", "산미 적당하고 깔끔해서 매일 마셔요", 5, "긍정", 0.93),
    (2, "도윤", "우유가 너무 많아서 커피 맛이 약해요", 2, "부정", 0.18),
    (5, "서연", "말차 향이 진하고 달지 않아서 좋아요", 5, "긍정", 0.91),
    (8, "지호", "꾸덕하고 맛있는데 양이 좀 아쉬움", 4, "긍정", 0.62),
    (4, "하은", "얼음이 금방 녹아서 밍밍했어요", 2, "부정", 0.21),
]


def seed_if_empty(conn):
    if crud.stats(conn)["menus"]:
        return
    for name, price, category in MENUS:
        crud.create_menu(conn, name, price, category)
    for menu_id, author, content, rating, label, score in REVIEWS:
        crud.create_review(conn, menu_id, author, content, rating, label, score)
