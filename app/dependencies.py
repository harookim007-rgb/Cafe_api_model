from fastapi import Request

from .database import connect


def get_db(request: Request):
    conn = connect(request.app.state.settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_sentiment(request: Request):
    return request.app.state.sentiment


def get_triton(request: Request):
    return request.app.state.triton


def get_llm(request: Request):
    return request.app.state.llm
