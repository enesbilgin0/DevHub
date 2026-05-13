"""Veri analiz sorguları (Postgres / SQLAlchemy async).

Her fonksiyon (headers, rows) tuple'ı döner. Bu sayede aynı sonuç hem rich
tablosu olarak terminale basılabilir hem de CSV'ye yazılabilir.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Result = tuple[list[str], list[tuple]]


async def most_active_users(session: AsyncSession, limit: int = 10) -> Result:
    sql = text("""
        SELECT u.id, u.username,
               COUNT(DISTINCT q.id) AS question_count,
               COUNT(DISTINCT a.id) AS answer_count,
               COUNT(DISTINCT q.id) + COUNT(DISTINCT a.id) AS total_activity,
               u.reputation
        FROM users u
        LEFT JOIN questions q ON q.user_id = u.id
        LEFT JOIN answers   a ON a.user_id = u.id
        GROUP BY u.id
        ORDER BY total_activity DESC, u.reputation DESC
        LIMIT :limit
    """)
    result = await session.execute(sql, {"limit": limit})
    headers = ["ID", "Kullanıcı", "Soru", "Cevap", "Toplam aktivite", "İtibar"]
    return headers, [tuple(r) for r in result.all()]


async def top_voted_questions(session: AsyncSession, limit: int = 10) -> Result:
    sql = text("""
        SELECT q.id, q.title, u.username,
               COALESCE(SUM(v.value), 0) AS score,
               COUNT(v.id) AS vote_count
        FROM questions q
        JOIN users u ON u.id = q.user_id
        LEFT JOIN votes v ON v.target_type = 'question' AND v.target_id = q.id
        GROUP BY q.id, u.username
        ORDER BY score DESC, vote_count DESC
        LIMIT :limit
    """)
    result = await session.execute(sql, {"limit": limit})
    headers = ["ID", "Başlık", "Yazar", "Net oy", "Toplam oy"]
    out = []
    for r in result.mappings().all():
        title = r["title"] if len(r["title"]) <= 60 else r["title"][:57] + "..."
        out.append((r["id"], title, r["username"], r["score"], r["vote_count"]))
    return headers, out


async def tag_distribution(session: AsyncSession, limit: int = 30) -> Result:
    sql = text("""
        SELECT t.name,
               COUNT(qt.question_id) AS question_count,
               (SELECT COUNT(*) FROM tag_follows tf WHERE tf.tag_id = t.id) AS follower_count,
               ROUND(
                 100.0 * COUNT(qt.question_id) /
                 NULLIF((SELECT COUNT(*) FROM question_tags), 0)::numeric, 2
               ) AS share_pct
        FROM tags t
        LEFT JOIN question_tags qt ON qt.tag_id = t.id
        GROUP BY t.id
        ORDER BY question_count DESC
        LIMIT :limit
    """)
    result = await session.execute(sql, {"limit": limit})
    headers = ["Etiket", "Soru sayısı", "Takipçi", "Pay (%)"]
    return headers, [tuple(r) for r in result.all()]


async def answers_per_question(session: AsyncSession) -> Result:
    sql = text("""
        WITH per_q AS (
            SELECT q.id, COUNT(a.id) AS ac
            FROM questions q
            LEFT JOIN answers a ON a.question_id = q.id
            GROUP BY q.id
        )
        SELECT
            COUNT(*)                                    AS question_count,
            ROUND(AVG(ac)::numeric, 2)                  AS avg_answers,
            MAX(ac)                                     AS max_answers,
            SUM(CASE WHEN ac = 0 THEN 1 ELSE 0 END)     AS unanswered
        FROM per_q
    """)
    row = (await session.execute(sql)).first()
    headers = ["Toplam soru", "Soru başına ort. cevap", "En çok cevaplı", "Cevapsız"]
    return headers, [tuple(row)]


async def signups_by_month(session: AsyncSession, limit: int = 24) -> Result:
    sql = text("""
        SELECT to_char(joined_at, 'YYYY-MM') AS month,
               COUNT(*) AS new_users
        FROM users
        GROUP BY month
        ORDER BY month DESC
        LIMIT :limit
    """)
    result = await session.execute(sql, {"limit": limit})
    headers = ["Ay", "Yeni kullanıcı"]
    return headers, [tuple(r) for r in result.all()]


async def acceptance_rate(session: AsyncSession) -> Result:
    sql = text("""
        SELECT
            COUNT(DISTINCT q.id) AS total_questions,
            COUNT(DISTINCT CASE WHEN a.is_accepted THEN q.id END) AS with_accepted,
            ROUND(
              100.0 * COUNT(DISTINCT CASE WHEN a.is_accepted THEN q.id END)
              / NULLIF(COUNT(DISTINCT q.id), 0)::numeric, 2
            ) AS acceptance_rate_pct
        FROM questions q
        LEFT JOIN answers a ON a.question_id = q.id
    """)
    row = (await session.execute(sql)).first()
    headers = ["Toplam soru", "Kabul edilmiş cevabı olan", "Kabul oranı (%)"]
    return headers, [tuple(row)]


REPORTS = {
    "active-users":    ("En aktif kullanıcılar",         most_active_users),
    "top-questions":   ("En çok oy alan sorular",        top_voted_questions),
    "tag-distribution":("Etiket dağılımı",               tag_distribution),
    "answers-per-q":   ("Soru başına cevap istatistiği", answers_per_question),
    "signups":         ("Aya göre kayıt",                signups_by_month),
    "acceptance-rate": ("Kabul edilen cevap oranı",      acceptance_rate),
}
