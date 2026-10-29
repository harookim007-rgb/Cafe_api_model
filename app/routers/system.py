from fastapi import APIRouter, Depends, Request

from .. import __version__, crud
from ..dependencies import get_db
from ..schemas import Stats

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@router.get("/ready")
async def ready(request: Request):
    state = request.app.state
    checks = {
        "database": True,
        "sentiment": state.sentiment.ready,
        "triton": await state.triton.is_ready(),
        "vllm": await state.llm.is_ready(),
    }
    ok = checks["database"] and checks["sentiment"]
    return {"status": "ok" if ok else "degraded", "checks": checks}


@router.get("/api/stats", response_model=Stats)
def get_stats(db=Depends(get_db)):
    return crud.stats(db)
