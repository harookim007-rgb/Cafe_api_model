import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class FakeSentiment:
    ready = True

    def predict(self, text):
        if "별로" in text or "아쉬" in text:
            return {"label": "부정", "score": 0.12}
        return {"label": "긍정", "score": 0.88}


class FakeTriton:
    async def is_ready(self):
        return True

    async def classify(self, raw, top_k=3):
        return [{"label": "Samoyed", "score": 0.91}, {"label": "Pomeranian", "score": 0.05}][:top_k]


class FakeLLM:
    async def is_ready(self):
        return True

    async def chat(self, messages, temperature=0.7, max_tokens=300):
        return {"content": "echo: " + messages[-1]["content"], "finish_reason": "stop", "usage": {}}


@pytest.fixture
def client(tmp_path):
    settings = Settings(db_path=str(tmp_path / "test.db"), sentiment_model=str(tmp_path / "x.joblib"))
    app = create_app(settings)
    with TestClient(app) as c:
        app.state.sentiment = FakeSentiment()
        app.state.triton = FakeTriton()
        app.state.llm = FakeLLM()
        yield c


@pytest.fixture
def menu(client):
    return client.post("/api/menus", json={"name": "아메리카노", "price": 4500}).json()
