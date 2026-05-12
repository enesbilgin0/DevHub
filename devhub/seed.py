"""Faker tabanlı sahte veri üretici.

Tek transaction içinde batch insert kullanarak hızlı şekilde:
- 100 kullanıcı
- ~30 etiket
- 500 soru (1-4 etiketli)
- 1200 cevap
- Rastgele oy ve takip ilişkileri
üretir.
"""
from __future__ import annotations

import random
import sqlite3

from faker import Faker

from .db import connect, init_schema, reset

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


def _insert_users(conn: sqlite3.Connection, fake: Faker, count: int) -> list[int]:
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
        rows.append((
            username,
            email,
            fake.sentence(nb_words=8),
            fake.date_time_between(start_date="-3y", end_date="now").isoformat(sep=" "),
            random.randint(0, 5000),
        ))
    conn.executemany(
        "INSERT INTO users (username, email, bio, joined_at, reputation) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    return [r[0] for r in conn.execute("SELECT id FROM users ORDER BY id").fetchall()]


def _insert_tags(conn: sqlite3.Connection) -> list[int]:
    conn.executemany(
        "INSERT INTO tags (name, description) VALUES (?, ?)",
        PREDEFINED_TAGS,
    )
    return [r[0] for r in conn.execute("SELECT id FROM tags ORDER BY id").fetchall()]


def _insert_questions(
    conn: sqlite3.Connection, fake: Faker, user_ids: list[int], tag_ids: list[int], count: int
) -> list[int]:
    q_rows = []
    for _ in range(count):
        q_rows.append((
            random.choice(user_ids),
            fake.sentence(nb_words=random.randint(6, 12)).rstrip("."),
            "\n\n".join(fake.paragraphs(nb=random.randint(2, 4))),
            fake.date_time_between(start_date="-2y", end_date="now").isoformat(sep=" "),
            random.randint(0, 5000),
        ))
    conn.executemany(
        "INSERT INTO questions (user_id, title, body, created_at, view_count) VALUES (?, ?, ?, ?, ?)",
        q_rows,
    )
    question_ids = [r[0] for r in conn.execute("SELECT id FROM questions ORDER BY id").fetchall()]

    qt_rows: list[tuple[int, int]] = []
    for qid in question_ids:
        for tid in random.sample(tag_ids, k=random.randint(1, 4)):
            qt_rows.append((qid, tid))
    conn.executemany(
        "INSERT OR IGNORE INTO question_tags (question_id, tag_id) VALUES (?, ?)",
        qt_rows,
    )
    return question_ids


def _insert_answers(
    conn: sqlite3.Connection, fake: Faker, user_ids: list[int], question_ids: list[int], count: int
) -> list[int]:
    rows = []
    accepted_per_question: dict[int, bool] = {}
    for _ in range(count):
        qid = random.choice(question_ids)
        is_accepted = 0
        if not accepted_per_question.get(qid) and random.random() < 0.35:
            is_accepted = 1
            accepted_per_question[qid] = True
        rows.append((
            qid,
            random.choice(user_ids),
            "\n\n".join(fake.paragraphs(nb=random.randint(1, 3))),
            fake.date_time_between(start_date="-2y", end_date="now").isoformat(sep=" "),
            is_accepted,
        ))
    conn.executemany(
        "INSERT INTO answers (question_id, user_id, body, created_at, is_accepted) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    return [r[0] for r in conn.execute("SELECT id FROM answers ORDER BY id").fetchall()]


def _insert_votes(
    conn: sqlite3.Connection,
    user_ids: list[int],
    question_ids: list[int],
    answer_ids: list[int],
) -> int:
    rows: set[tuple[int, str, int, int]] = set()
    for qid in question_ids:
        voters = random.sample(user_ids, k=random.randint(0, min(20, len(user_ids))))
        for uid in voters:
            value = 1 if random.random() < 0.85 else -1
            rows.add((uid, "question", qid, value))
    for aid in answer_ids:
        voters = random.sample(user_ids, k=random.randint(0, min(15, len(user_ids))))
        for uid in voters:
            value = 1 if random.random() < 0.8 else -1
            rows.add((uid, "answer", aid, value))
    conn.executemany(
        "INSERT OR IGNORE INTO votes (user_id, target_type, target_id, value) VALUES (?, ?, ?, ?)",
        list(rows),
    )
    return len(rows)


def _insert_follows(
    conn: sqlite3.Connection, user_ids: list[int], tag_ids: list[int]
) -> tuple[int, int]:
    user_pairs: set[tuple[int, int]] = set()
    for uid in user_ids:
        k = random.randint(0, 10)
        for target in random.sample([x for x in user_ids if x != uid], k=min(k, len(user_ids) - 1)):
            user_pairs.add((uid, target))
    conn.executemany(
        "INSERT OR IGNORE INTO user_follows (follower_id, followed_id) VALUES (?, ?)",
        list(user_pairs),
    )

    tag_pairs: set[tuple[int, int]] = set()
    for uid in user_ids:
        for tid in random.sample(tag_ids, k=random.randint(0, min(6, len(tag_ids)))):
            tag_pairs.add((uid, tid))
    conn.executemany(
        "INSERT OR IGNORE INTO tag_follows (user_id, tag_id) VALUES (?, ?)",
        list(tag_pairs),
    )
    return len(user_pairs), len(tag_pairs)


def run(
    *,
    users: int = DEFAULT_USERS,
    questions: int = DEFAULT_QUESTIONS,
    answers: int = DEFAULT_ANSWERS,
    seed: int | None = 42,
    db_path=None,
) -> dict[str, int]:
    """Veritabanını sıfırlayıp sahte veri üretir. İstatistikleri döner."""
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)
    fake = Faker()

    if db_path is None:
        from .db import DEFAULT_DB_PATH
        db_path = DEFAULT_DB_PATH
    reset(db_path)

    with connect(db_path) as conn:
        init_schema(conn)
        conn.execute("BEGIN")
        try:
            user_ids = _insert_users(conn, fake, users)
            tag_ids = _insert_tags(conn)
            question_ids = _insert_questions(conn, fake, user_ids, tag_ids, questions)
            answer_ids = _insert_answers(conn, fake, user_ids, question_ids, answers)
            vote_count = _insert_votes(conn, user_ids, question_ids, answer_ids)
            user_follow_count, tag_follow_count = _insert_follows(conn, user_ids, tag_ids)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return {
        "users": len(user_ids),
        "tags": len(tag_ids),
        "questions": len(question_ids),
        "answers": len(answer_ids),
        "votes": vote_count,
        "user_follows": user_follow_count,
        "tag_follows": tag_follow_count,
    }
