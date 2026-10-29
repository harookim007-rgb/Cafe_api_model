import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .clients.triton import TritonClient
from .clients.vllm import VLLMClient
from .config import Settings, settings as default_settings
from .crud import Duplicate, NotFound
from .database import connect, init_db
from .routers import ai, menus, reviews, system
from .seed import seed_if_empty
from .sentiment import SentimentModel

STATIC_DIR = Path(__file__).parent / "static"
LABELS = Path(__file__).parent / "resources" / "imagenet_classes.json"

log = logging.getLogger("cafe")


def create_app(settings: Settings = default_settings) -> FastAPI:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        init_db(settings.db_path)
        if settings.seed_demo:
            conn = connect(settings.db_path)
            try:
                seed_if_empty(conn)
            finally:
                conn.close()

        app.state.sentiment = SentimentModel(settings.sentiment_model)
        app.state.sentiment.load()
        app.state.triton = TritonClient(settings.triton_url, settings.triton_model, LABELS, settings.timeout)
        app.state.llm = VLLMClient(settings.vllm_url, settings.llm_model, settings.timeout)
        log.info("started (env=%s, db=%s)", settings.env, settings.db_path)
        yield

    app = FastAPI(title="Cafe AI", version=__version__, lifespan=lifespan)

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:8]
        t0 = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        response.headers["x-request-id"] = rid
        if request.url.path.startswith("/api") or request.url.path in ("/health", "/ready"):
            log.info("%s %s %s %d %.1fms", rid, request.method, request.url.path, response.status_code, ms)
        return response

    @app.exception_handler(NotFound)
    async def not_found(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(Duplicate)
    async def duplicate(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    for r in (system.router, menus.router, reviews.router, ai.router):
        app.include_router(r)

    # 관리자 화면 (API 라우트 뒤에 마운트해야 /api 가 가려지지 않음)
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
