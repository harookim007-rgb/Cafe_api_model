import io
import json

import httpx
import numpy as np
from PIL import Image

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess(raw: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(raw)).convert("RGB").resize((224, 224))
    x = (np.asarray(img, dtype=np.float32) / 255 - MEAN) / STD
    return x.transpose(2, 0, 1)[np.newaxis]


def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


class TritonClient:
    def __init__(self, url, model, labels_path, timeout=30):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.labels = json.loads(open(labels_path, encoding="utf-8").read())

    async def is_ready(self):
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                r = await client.get(f"{self.url}/v2/models/{self.model}/ready")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def classify(self, raw: bytes, top_k=3):
        x = preprocess(raw)
        payload = {
            "inputs": [{"name": "input", "shape": list(x.shape), "datatype": "FP32",
                        "data": x.ravel().tolist()}]
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.url}/v2/models/{self.model}/infer", json=payload)
            r.raise_for_status()
        logits = np.array(r.json()["outputs"][0]["data"], dtype=np.float32)
        probs = softmax(logits)
        top = probs.argsort()[::-1][:top_k]
        return [{"label": self.labels[i], "score": round(float(probs[i]), 4)} for i in top]
