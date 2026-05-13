"""Faker tabanlı sahte veri üretici (PostgreSQL + SQLAlchemy async).

Tek transaction içinde batch insert ile:
- 100 kullanıcı
- ~30 etiket
- 500 soru (1-4 etiketli)
- 1200 cevap
- Rastgele oy ve takip ilişkileri
üretir.
"""
from __future__ import annotations

import asyncio
import random

from faker import Faker
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import session_scope
from .models import (
    Answer,
    Question,
    QuestionTag,
    Tag,
    TagFollow,
    User,
    UserFollow,
    Vote,
)

DEFAULT_USERS = 100
DEFAULT_QUESTIONS = 500
DEFAULT_ANSWERS = 1200

PREDEFINED_TAGS: list[tuple[str, str]] = [
    ("python", "Python programlama dili"),
    ("javascript", "JavaScript ve tarayıcı tarafı"),
    ("typescript", "TypeScript tip sistemi ve dil özellikleri"),
    ("sqlite", "SQLite gömülü veritabanı"),
    ("postgresql", "PostgreSQL ilişkisel veritabanı"),
    ("docker", "Konteyner ve imaj yönetimi"),
    ("kubernetes", "Konteyner orkestrasyonu"),
    ("react", "React UI kütüphanesi"),
    ("nextjs", "Next.js framework"),
    ("django", "Django web framework"),
    ("flask", "Flask mikro framework"),
    ("fastapi", "FastAPI Python web framework"),
    ("go", "Go programlama dili"),
    ("rust", "Rust sistem dili"),
    ("linux", "Linux işletim sistemi"),
    ("bash", "Bash kabuk programlama"),
    ("git", "Git sürüm kontrolü"),
    ("ci-cd", "Sürekli entegrasyon ve dağıtım"),
    ("aws", "Amazon Web Services"),
    ("gcp", "Google Cloud Platform"),
    ("redis", "Redis bellek içi veri deposu"),
    ("kafka", "Apache Kafka mesaj kuyruğu"),
    ("graphql", "GraphQL sorgu dili"),
    ("rest-api", "REST API tasarımı"),
    ("testing", "Test stratejileri ve araçları"),
    ("performance", "Performans optimizasyonu"),
    ("security", "Güvenlik konuları"),
    ("algorithms", "Algoritma ve veri yapıları"),
    ("design-patterns", "Yazılım tasarım kalıpları"),
    ("debugging", "Hata ayıklama teknikleri"),
]


async def _truncate_all(session: AsyncSession) -> None:
    """FK kısıtlarına dokunmadan tüm tabloları boşalt (silme sırası önemli)."""
    for model in (
        Vote,
        TagFollow,
        UserFollow,
        QuestionTag,
        Answer,
        Question,
        Tag,
        User,
    ):
        await session.execute(delete(model))


async def _insert_users(session: AsyncSession, fake: Faker, count: int) -> list[int]:
    rows = []
    seen_usernames: set[str] = set()
    seen_emails: set[str] = set()
    while len(rows) < count:
        username = fake.unique.user_name()
        email = fake.unique.email()
        if username in seen_usernames or email in seen_emails:
            continue
        seen_usernames.add(username)
        seen_emails.add(email)
        rows.append({
            "username": username,
            "email": email,
            "bio": fake.sentence(nb_words=8),
            "joined_at": fake.date_time_between(start_date="-3y", end_date="now"),
            "reputation": random.randint(0, 5000),
        })
    await session.execute(insert(User), rows)
    result = await session.execute(select(User.id).order_by(User.id))
    return list(result.scalars().all())


async def _insert_tags(session: AsyncSession) -> list[int]:
    rows = [{"name": n, "description": d} for n, d in PREDEFINED_TAGS]
    await session.execute(insert(Tag), rows)
    result = await session.execute(select(Tag.id).order_by(Tag.id))
    return list(result.scalars().all())


async def _insert_questions(
    session: AsyncSession,
    fake: Faker,
    user_ids: list[int],
    tag_ids: list[int],
    count: int,
) -> list[int]:
    q_rows = []
    for _ in range(count):
        q_rows.append({
            "user_id": random.choice(user_ids),
            "title": fake.sentence(nb_words=random.randint(6, 12)).rstrip("."),
            "body": "\n\n".join(fake.paragraphs(nb=random.randint(2, 4))),
            "created_at": fake.date_time_between(start_date="-2y", end_date="now"),
            "view_count": random.randint(0, 5000),
        })
    await session.execute(insert(Question), q_rows)
    result = await session.execute(select(Question.id).order_by(Question.id))
    question_ids = list(result.scalars().all())

    qt_pairs: set[tuple[int, int]] = set()
    for qid in question_ids:
        for tid in random.sample(tag_ids, k=random.randint(1, 4)):
            qt_pairs.add((qid, tid))
    qt_rows = [{"question_id": q, "tag_id": t} for q, t in qt_pairs]
    await session.execute(insert(QuestionTag), qt_rows)
    return question_ids


async def _insert_answers(
    session: AsyncSession,
    fake: Faker,
    user_ids: list[int],
    question_ids: list[int],
    count: int,
) -> list[int]:
    rows = []
    accepted_per_question: dict[int, bool] = {}
    for _ in range(count):
        qid = random.choice(question_ids)
        is_accepted = False
        if not accepted_per_question.get(qid) and random.random() < 0.35:
            is_accepted = True
            accepted_per_question[qid] = True
        rows.append({
            "question_id": qid,
            "user_id": random.choice(user_ids),
            "body": "\n\n".join(fake.paragraphs(nb=random.randint(1, 3))),
            "created_at": fake.date_time_between(start_date="-2y", end_date="now"),
            "is_accepted": is_accepted,
        })
    await session.execute(insert(Answer), rows)
    result = await session.execute(select(Answer.id).order_by(Answer.id))
    return list(result.scalars().all())


async def _insert_votes(
    session: AsyncSession,
    user_ids: list[int],
    question_ids: list[int],
    answer_ids: list[int],
) -> int:
    seen: set[tuple[int, str, int]] = set()
    rows: list[dict] = []
    for qid in question_ids:
        voters = random.sample(user_ids, k=random.randint(0, min(20, len(user_ids))))
        for uid in voters:
            key = (uid, "question", qid)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "user_id": uid,
                "target_type": "question",
                "target_id": qid,
                "value": 1 if random.random() < 0.85 else -1,
            })
    for aid in answer_ids:
        voters = random.sample(user_ids, k=random.randint(0, min(15, len(user_ids))))
        for uid in voters:
            key = (uid, "answer", aid)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "user_id": uid,
                "target_type": "answer",
                "target_id": aid,
                "value": 1 if random.random() < 0.8 else -1,
            })
    if rows:
        await session.execute(insert(Vote), rows)
    return len(rows)


async def _insert_follows(
    session: AsyncSession, user_ids: list[int], tag_ids: list[int]
) -> tuple[int, int]:
    user_pairs: set[tuple[int, int]] = set()
    for uid in user_ids:
        k = random.randint(0, 10)
        for target in random.sample([x for x in user_ids if x != uid], k=min(k, len(user_ids) - 1)):
            user_pairs.add((uid, target))
    if user_pairs:
        await session.execute(
            insert(UserFollow),
            [{"follower_id": a, "followed_id": b} for a, b in user_pairs],
        )

    tag_pairs: set[tuple[int, int]] = set()
    for uid in user_ids:
        for tid in random.sample(tag_ids, k=random.randint(0, min(6, len(tag_ids)))):
            tag_pairs.add((uid, tid))
    if tag_pairs:
        await session.execute(
            insert(TagFollow),
            [{"user_id": u, "tag_id": t} for u, t in tag_pairs],
        )
    return len(user_pairs), len(tag_pairs)


async def run_async(
    *,
    users: int = DEFAULT_USERS,
    questions: int = DEFAULT_QUESTIONS,
    answers: int = DEFAULT_ANSWERS,
    seed: int | None = 42,
) -> dict[str, int]:
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)
    fake = Faker()

    async with session_scope() as session:
        await _truncate_all(session)
        user_ids = await _insert_users(session, fake, users)
        tag_ids = await _insert_tags(session)
        question_ids = await _insert_questions(session, fake, user_ids, tag_ids, questions)
        answer_ids = await _insert_answers(session, fake, user_ids, question_ids, answers)
        vote_count = await _insert_votes(session, user_ids, question_ids, answer_ids)
        user_follow_count, tag_follow_count = await _insert_follows(session, user_ids, tag_ids)

    return {
        "users": len(user_ids),
        "tags": len(tag_ids),
        "questions": len(question_ids),
        "answers": len(answer_ids),
        "votes": vote_count,
        "user_follows": user_follow_count,
        "tag_follows": tag_follow_count,
    }


def run(
    *,
    users: int = DEFAULT_USERS,
    questions: int = DEFAULT_QUESTIONS,
    answers: int = DEFAULT_ANSWERS,
    seed: int | None = 42,
) -> dict[str, int]:
    """Senkron entry point — CLI'den çağrılır."""
    return asyncio.run(
        run_async(users=users, questions=questions, answers=answers, seed=seed)
    )
