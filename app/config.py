import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default):
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: env("APP_ENV", "local"))
    log_level: str = field(default_factory=lambda: env("LOG_LEVEL", "INFO"))
    db_path: str = field(default_factory=lambda: env("DB_PATH", str(BASE_DIR / "data" / "cafe.db")))
    sentiment_model: str = field(
        default_factory=lambda: env("SENTIMENT_MODEL", str(BASE_DIR / "models" / "sentiment.joblib"))
    )
    triton_url: str = field(default_factory=lambda: env("TRITON_URL", "http://localhost:8000"))
    triton_model: str = field(default_factory=lambda: env("TRITON_MODEL", "resnet18"))
    vllm_url: str = field(default_factory=lambda: env("VLLM_URL", "http://localhost:8100"))
    llm_model: str = field(default_factory=lambda: env("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"))
    timeout: float = field(default_factory=lambda: float(env("UPSTREAM_TIMEOUT", "30")))
    max_upload_mb: int = field(default_factory=lambda: int(env("MAX_UPLOAD_MB", "5")))
    seed_demo: bool = field(default_factory=lambda: env("SEED_DEMO", "0") == "1")


settings = Settings()
