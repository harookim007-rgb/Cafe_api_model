import logging
from pathlib import Path

import joblib

log = logging.getLogger(__name__)


class SentimentModel:
    def __init__(self, path):
        self.path = Path(path)
        self.model = None

    def load(self):
        if not self.path.exists():
            log.warning("sentiment model not found: %s (run scripts/train_sentiment.py)", self.path)
            return
        self.model = joblib.load(self.path)
        log.info("sentiment model loaded: %s", self.path.name)

    @property
    def ready(self):
        return self.model is not None

    def predict(self, text):
        p = float(self.model.predict_proba([text])[0][1])
        return {"label": "긍정" if p >= 0.5 else "부정", "score": round(p, 4)}
