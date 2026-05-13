"""Genel istatistik alt komutu."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table
from sqlalchemy import text

from ..db import session_scope
from . import run_async

console = Console()


async def _fetch_counts() -> dict[str, int]:
    sql = text("""
        SELECT
          (SELECT COUNT(*) FROM users)         AS users,
          (SELECT COUNT(*) FROM questions)     AS questions,
          (SELECT COUNT(*) FROM answers)       AS answers,
          (SELECT COUNT(*) FROM tags)          AS tags,
          (SELECT COUNT(*) FROM votes)         AS votes,
          (SELECT COUNT(*) FROM user_follows)  AS user_follows,
          (SELECT COUNT(*) FROM tag_follows)   AS tag_follows,
          (SELECT COUNT(*) FROM answers WHERE is_accepted) AS accepted
    """)
    async with session_scope() as session:
        row = (await session.execute(sql)).mappings().first()
    return dict(row)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("stats", help="Platform geneli istatistikler")
    p.set_defaults(func=cmd_stats)


def cmd_stats(args: argparse.Namespace) -> int:
    counts = run_async(_fetch_counts())
    labels = [
        ("Kullanıcılar", "users"),
        ("Sorular", "questions"),
        ("Cevaplar", "answers"),
        ("Etiketler", "tags"),
        ("Oylar", "votes"),
        ("Kullanıcı takipleri", "user_follows"),
        ("Etiket takipleri", "tag_follows"),
        ("Kabul edilmiş cevap", "accepted"),
    ]
    table = Table(title="DevHub — Genel İstatistikler", header_style="bold cyan")
    table.add_column("Metrik", style="bold")
    table.add_column("Değer", justify="right", style="yellow")
    for label, key in labels:
        table.add_row(label, f"{counts[key]:,}")
    console.print(table)
    return 0
