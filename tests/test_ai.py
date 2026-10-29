import io

import numpy as np
from PIL import Image

from app.clients.triton import preprocess, softmax


def png():
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_sentiment(client):
    r = client.post("/api/ai/sentiment", json={"text": "별로예요"})
    assert r.json()["label"] == "부정"


def test_classify(client):
    r = client.post("/api/ai/classify", files={"file": ("dog.png", png(), "image/png")})
    assert r.status_code == 200
    assert r.json()["labels"][0]["label"] == "Samoyed"


def test_classify_rejects_non_image(client):
    r = client.post("/api/ai/classify", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_describe(client):
    r = client.post("/api/ai/describe", files={"file": ("dog.png", png(), "image/png")})
    assert r.json()["label"] == "Samoyed"
    assert r.json()["description"].startswith("echo:")


def test_chat(client):
    r = client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "안녕"}]})
    assert r.json()["content"] == "echo: 안녕"


def test_chat_rejects_unknown_role(client):
    r = client.post("/api/ai/chat", json={"messages": [{"role": "admin", "content": "x"}]})
    assert r.status_code == 422


def test_model_server_down(client):
    from app.clients.vllm import VLLMClient

    client.app.state.llm = VLLMClient("http://127.0.0.1:9", "m", timeout=1)
    r = client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 503
    # 모델 서버가 죽어도 메뉴 API 는 동작해야 함
    assert client.get("/api/menus").status_code == 200


def test_preprocess():
    x = preprocess(png())
    assert x.shape == (1, 3, 224, 224) and x.dtype == np.float32
    assert abs(softmax(np.array([1.0, 2.0, 3.0])).sum() - 1) < 1e-6
