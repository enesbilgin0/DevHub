"""Pydantic v2 şemaları."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth -----------------------------------------------------------------

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    bio: str | None = Field(default=None, max_length=500)


class LoginIn(BaseModel):
    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime


# --- User -----------------------------------------------------------------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    bio: str | None = None
    joined_at: datetime
    reputation: int


class UserSummary(BaseModel):
    """Response içinde gömülmek için sade kullanıcı bilgisi."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    reputation: int


# --- Tags -----------------------------------------------------------------

class TagCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    description: str | None = Field(default=None, max_length=500)


class TagOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    question_count: int = 0


# --- Questions ------------------------------------------------------------

class QuestionCreate(BaseModel):
    title: str = Field(min_length=10, max_length=300)
    body: str = Field(min_length=20, max_length=20000)
    tags: list[str] = Field(default_factory=list, max_length=5)


class QuestionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=10, max_length=300)
    body: str | None = Field(default=None, min_length=20, max_length=20000)
    tags: list[str] | None = Field(default=None, max_length=5)


class QuestionSummary(BaseModel):
    """Listeleme için gerekli alanlar."""

    id: int
    title: str
    author: UserSummary
    tags: list[str]
    created_at: datetime
    view_count: int
    vote_score: int
    answer_count: int
    has_accepted: bool


class QuestionDetail(QuestionSummary):
    body: str


# --- Answers --------------------------------------------------------------

class AnswerCreate(BaseModel):
    body: str = Field(min_length=10, max_length=20000)


class AnswerUpdate(BaseModel):
    body: str = Field(min_length=10, max_length=20000)


class AnswerOut(BaseModel):
    id: int
    question_id: int
    author: UserSummary
    body: str
    created_at: datetime
    is_accepted: bool
    vote_score: int


# --- Votes ----------------------------------------------------------------

class VoteIn(BaseModel):
    value: int = Field(description="1 (up) veya -1 (down)")

    def __init__(self, **data):
        super().__init__(**data)
        if self.value not in (-1, 1):
            raise ValueError("value must be -1 or 1")


class VoteOut(BaseModel):
    target_type: str
    target_id: int
    value: int
    score: int


# --- Pagination -----------------------------------------------------------

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
