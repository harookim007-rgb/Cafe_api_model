import time

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from ..dependencies import get_llm, get_sentiment, get_triton
from ..schemas import ChatIn, ChatOut, ClassifyOut, DescribeOut, SentimentOut, TextIn

router = APIRouter(prefix="/api/ai", tags=["ai"])

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DESCRIBE_PROMPT = "너는 사진 속 사물을 쉽게 설명해 주는 해설가야. 한국어로 두 문장만 말해."


def elapsed(t0):
    return round((time.perf_counter() - t0) * 1000, 1)


async def read_image(request: Request, file: UploadFile) -> bytes:
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(415, "jpg, png, webp 이미지만 올릴 수 있습니다")
    raw = await file.read()
    limit = request.app.state.settings.max_upload_mb
    if len(raw) > limit * 1024 * 1024:
        raise HTTPException(413, f"{limit}MB 이하 이미지만 올릴 수 있습니다")
    return raw


@router.post("/sentiment", response_model=SentimentOut)
def sentiment(body: TextIn, model=Depends(get_sentiment)):
    if not model.ready:
        raise HTTPException(503, "감성 분석 모델이 아직 준비되지 않았습니다")
    t0 = time.perf_counter()
    return {**model.predict(body.text), "ms": elapsed(t0)}


@router.post("/classify", response_model=ClassifyOut)
async def classify(request: Request, file: UploadFile = File(...), triton=Depends(get_triton)):
    raw = await read_image(request, file)
    t0 = time.perf_counter()
    try:
        labels = await triton.classify(raw)
    except httpx.HTTPError:
        raise HTTPException(503, "이미지 분류 서버(Triton)에 연결할 수 없습니다")
    return {"labels": labels, "ms": elapsed(t0)}


@router.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn, llm=Depends(get_llm)):
    t0 = time.perf_counter()
    try:
        out = await llm.chat([m.model_dump() for m in body.messages], body.temperature, body.max_tokens)
    except httpx.HTTPError:
        raise HTTPException(503, "LLM 서버(vLLM)에 연결할 수 없습니다")
    return {**out, "ms": elapsed(t0)}


@router.post("/describe", response_model=DescribeOut)
async def describe(
    request: Request,
    file: UploadFile = File(...),
    triton=Depends(get_triton),
    llm=Depends(get_llm),
):
    raw = await read_image(request, file)
    try:
        top = (await triton.classify(raw, top_k=1))[0]
        out = await llm.chat(
            [
                {"role": "system", "content": DESCRIBE_PROMPT},
                {"role": "user", "content": f"{top['label']} 에 대해 설명해 줘."},
            ],
            temperature=0,
            max_tokens=160,
        )
    except httpx.HTTPError:
        raise HTTPException(503, "모델 서버에 연결할 수 없습니다")
    return {"label": top["label"], "score": top["score"], "description": out["content"]}
