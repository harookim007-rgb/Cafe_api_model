import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS menus (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    price       INTEGER NOT NULL CHECK (price > 0),
    category    TEXT    NOT NULL DEFAULT '커피',
    is_soldout  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id          INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    author           TEXT    NOT NULL,
    content          TEXT    NOT NULL,
    rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    sentiment        TEXT,
    sentiment_score  REAL,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_reviews_menu_id ON reviews(menu_id);
"""


def init_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)


def connect(path):
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn):
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise
