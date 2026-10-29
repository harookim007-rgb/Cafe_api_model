from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["커피", "논커피", "티", "디저트"]


class MenuIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    price: int = Field(gt=0, le=200_000)
    category: Category = "커피"


class MenuPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=40)
    price: int | None = Field(None, gt=0, le=200_000)
    category: Category | None = None
    is_soldout: bool | None = None


class Menu(BaseModel):
    id: int
    name: str
    price: int
    category: str
    is_soldout: bool
    created_at: str
    review_count: int = 0
    avg_rating: float | None = None
    avg_sentiment: float | None = None


class ReviewIn(BaseModel):
    menu_id: int
    author: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=2, max_length=500)
    rating: int = Field(ge=1, le=5)


class Review(BaseModel):
    id: int
    menu_id: int
    menu_name: str | None = None
    author: str
    content: str
    rating: int
    sentiment: str | None
    sentiment_score: float | None
    created_at: str


class Stats(BaseModel):
    menus: int
    reviews: int
    avg_rating: float | None
    positive_ratio: float | None


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class SentimentOut(BaseModel):
    label: str
    score: float
    ms: float


class Label(BaseModel):
    label: str
    score: float


class ClassifyOut(BaseModel):
    labels: list[Label]
    ms: float


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatIn(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=40)
    temperature: float = Field(0.7, ge=0, le=1.5)
    max_tokens: int = Field(300, ge=1, le=1024)


class ChatOut(BaseModel):
    content: str
    finish_reason: str | None = None
    usage: dict = {}
    ms: float


class DescribeOut(BaseModel):
    label: str
    score: float
    description: str
