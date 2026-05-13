"""FastAPI uygulaması — `uvicorn devhub.api.main:app` ile çalıştırılır."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..db import dispose_engine
from .cache import close_redis
from .routers import answers, auth, questions, tags


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()
    await dispose_engine()


app = FastAPI(
    title="DevHub API",
    description="Geliştiricilerin etkileşim kurabileceği soru-cevap platformu.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(tags.router)
app.include_router(questions.router)
app.include_router(answers.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
