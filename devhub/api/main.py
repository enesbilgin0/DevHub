"""FastAPI uygulaması — `uvicorn devhub.api.main:app` ile çalıştırılır."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..db import dispose_engine
from .routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_engine()


app = FastAPI(
    title="DevHub API",
    description="Geliştiricilerin etkileşim kurabileceği soru-cevap platformu.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(auth.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
