"""FastAPI uygulaması — `uvicorn devhub.api.main:app` ile çalıştırılır."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..db import dispose_engine
from .cache import close_redis
from .routers import answers, auth, comments, questions, tags, users, ws

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": (
            "Kullanıcı kaydı, giriş ve token yönetimi. Access JWT (15 dk) + refresh JWT (7 gün)."
            " Refresh token rotation: kullanılan refresh revoke edilir, yeni jti üretilir."
        ),
    },
    {
        "name": "tags",
        "description": "Etiketler — listeleme (sayfalama, sıralama, arama), detay, oluşturma.",
    },
    {
        "name": "questions",
        "description": (
            "Sorular için CRUD + oylama. Liste sıralanabilir (created/votes/views/answers),"
            " etiket veya yazara göre filtrelenebilir."
        ),
    },
    {
        "name": "answers",
        "description": "Cevaplar için CRUD + kabul + oylama. Sadece soru sahibi cevap kabul edebilir.",
    },
    {
        "name": "comments",
        "description": (
            "Soru veya cevap altına düz metin yorumlar. Düzenleme yok; sadece sahip silebilir."
            " Body 5–600 karakter."
        ),
    },
    {
        "name": "realtime",
        "description": (
            "WebSocket bildirim akışı. `?token=<access_jwt>` ile bağlanın; cevap yazma,"
            " kabul ve oylama olayları gerçek zamanlı yayılır."
        ),
    },
    {
        "name": "users",
        "description": "Public kullanıcı profili — istatistik, rozet ve günlük katkı aktivitesi.",
    },
    {"name": "meta", "description": "Sağlık kontrolü gibi servis-içi endpoint'ler."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()
    await dispose_engine()


app = FastAPI(
    title="DevHub API",
    summary="Geliştiricilerin etkileşim kurabileceği soru-cevap platformu.",
    description=(
        "DevHub; soru sorma, cevap yazma, etiketleme, oylama ve kabul akışlarını sağlayan"
        " bir Q&A platformudur. Gerçek zamanlı bildirimler için WebSocket akışı bulunur."
        "\n\n**Auth akışı:** `/auth/register` veya `/auth/login` → access + refresh token."
        " Access süresi dolduğunda `/auth/refresh` ile yenileyin."
        " Swagger UI üzerinden 'Authorize' butonunu kullanmak için `/auth/token` form endpoint'i sağlanmıştır."
    ),
    version="0.2.0",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    contact={"name": "DevHub", "url": "https://github.com/enesbilgin0/DevHub"},
    license_info={"name": "MIT"},
)

app.include_router(auth.router)
app.include_router(tags.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(comments.router)
app.include_router(users.router)
app.include_router(ws.router)


@app.get("/health", tags=["meta"], summary="Servis sağlık kontrolü")
async def health() -> dict[str, str]:
    return {"status": "ok"}
