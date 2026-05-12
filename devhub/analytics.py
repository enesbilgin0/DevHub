"""Veri analiz sorguları.

Her fonksiyon (headers, rows) tuple'ı döner. Bu sayede aynı sonuç hem rich
tablosu olarak terminale basılabilir hem de CSV'ye yazılabilir.
"""
from __future__ import annotations

import sqlite3

Result = tuple[list[str], list[tuple]]


def most_active_users(conn: sqlite3.Connection, limit: int = 10) -> Result:
    sql = """
        SELECT u.id, u.username,
               COUNT(DISTINCT q.id) AS question_count,
               COUNT(DISTINCT a.id) AS answer_count,
               COUNT(DISTINCT q.id) + COUNT(DISTINCT a.id) AS total_activity,
               u.reputation
        FROM users u
        LEFT JOIN questions q ON q.user_id = u.id
        LEFT JOIN answers  a  ON a.user_id = u.id
        GROUP BY u.id
        ORDER BY total_activity DESC, u.reputation DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (limit,)).fetchall()
    headers = ["ID", "Kullanıcı", "Soru", "Cevap", "Toplam aktivite", "İtibar"]
    return headers, [tuple(r) for r in rows]


def top_voted_questions(conn: sqlite3.Connection, limit: int = 10) -> Result:
    sql = """
        SELECT q.id, q.title, u.username,
               COALESCE(SUM(v.value), 0) AS score,
               COUNT(v.id) AS vote_count
        FROM questions q
        JOIN users u ON u.id = q.user_id
        LEFT JOIN votes v ON v.target_type = 'question' AND v.target_id = q.id
        GROUP BY q.id
        ORDER BY score DESC, vote_count DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (limit,)).fetchall()
    headers = ["ID", "Başlık", "Yazar", "Net oy", "Toplam oy"]
    out = []
    for r in rows:
        title = r["title"] if len(r["title"]) <= 60 else r["title"][:57] + "..."
        out.append((r["id"], title, r["username"], r["score"], r["vote_count"]))
    return headers, out


def tag_distribution(conn: sqlite3.Connection, limit: int = 30) -> Result:
    sql = """
        SELECT t.name,
               COUNT(qt.question_id) AS question_count,
               (SELECT COUNT(*) FROM tag_follows tf WHERE tf.tag_id = t.id) AS follower_count,
               ROUND(
                 100.0 * COUNT(qt.question_id) /
                 (SELECT COUNT(*) FROM question_tags), 2
               ) AS share_pct
        FROM tags t
        LEFT JOIN question_tags qt ON qt.tag_id = t.id
        GROUP BY t.id
        ORDER BY question_count DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (limit,)).fetchall()
    headers = ["Etiket", "Soru sayısı", "Takipçi", "Pay (%)"]
    return headers, [tuple(r) for r in rows]


def answers_per_question(conn: sqlite3.Connection) -> Result:
    sql = """
        WITH per_q AS (
            SELECT q.id, COUNT(a.id) AS ac
            FROM questions q
            LEFT JOIN answers a ON a.question_id = q.id
            GROUP BY q.id
        )
        SELECT
            COUNT(*) AS question_count,
            ROUND(AVG(ac), 2) AS avg_answers,
            MAX(ac) AS max_answers,
            SUM(CASE WHEN ac = 0 THEN 1 ELSE 0 END) AS unanswered
        FROM per_q
    """
    row = conn.execute(sql).fetchone()
    headers = ["Toplam soru", "Soru başına ort. cevap", "En çok cevaplı", "Cevapsız"]
    return headers, [tuple(row)]


def signups_by_month(conn: sqlite3.Connection, limit: int = 24) -> Result:
    sql = """
        SELECT strftime('%Y-%m', joined_at) AS month,
               COUNT(*) AS new_users
        FROM users
        GROUP BY month
        ORDER BY month DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (limit,)).fetchall()
    headers = ["Ay", "Yeni kullanıcı"]
    return headers, [tuple(r) for r in rows]


def acceptance_rate(conn: sqlite3.Connection) -> Result:
    sql = """
        SELECT
            COUNT(DISTINCT q.id) AS total_questions,
            COUNT(DISTINCT CASE WHEN a.is_accepted = 1 THEN q.id END) AS with_accepted,
            ROUND(
              100.0 * COUNT(DISTINCT CASE WHEN a.is_accepted = 1 THEN q.id END)
              / NULLIF(COUNT(DISTINCT q.id), 0), 2
            ) AS acceptance_rate_pct
        FROM questions q
        LEFT JOIN answers a ON a.question_id = q.id
    """
    row = conn.execute(sql).fetchone()
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
