import logging
from typing import Literal

from fastapi import APIRouter, Depends, Query

from .. import crud
from ..dependencies import get_db, get_sentiment
from ..schemas import Review, ReviewIn

router = APIRouter(prefix="/api/reviews", tags=["reviews"])
log = logging.getLogger(__name__)


@router.get("", response_model=list[Review])
def list_reviews(
    menu_id: int | None = None,
    sentiment: Literal["긍정", "부정"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    return crud.list_reviews(db, menu_id, sentiment, limit)


@router.post("", response_model=Review, status_code=201)
def create_review(body: ReviewIn, db=Depends(get_db), model=Depends(get_sentiment)):
    label = score = None
    if model.ready:
        result = model.predict(body.content)
        label, score = result["label"], result["score"]
    else:
        # 모델이 없어도 리뷰 저장은 되게
        log.warning("review saved without sentiment (menu_id=%s)", body.menu_id)
    return crud.create_review(db, body.menu_id, body.author, body.content, body.rating, label, score)


@router.delete("/{review_id}", response_model=Review)
def delete_review(review_id: int, db=Depends(get_db)):
    return crud.delete_review(db, review_id)
