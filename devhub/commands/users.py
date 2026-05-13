"""Kullanıcı yönetim alt komutları."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table
from sqlalchemy import text

from ..db import session_scope
from . import run_async

console = Console()

SORT_COLUMNS = {
    "joined": "joined_at",
    "username": "username",
    "reputation": "reputation",
    "id": "id",
}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("users", help="Kullanıcı işlemleri")
    sub = p.add_subparsers(dest="users_action", required=True)

    p_list = sub.add_parser("list", help="Kullanıcıları listele")
    p_list.add_argument("--sort", choices=SORT_COLUMNS.keys(), default="joined")
    p_list.add_argument("--desc", action="store_true", help="Azalan sırala")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Bir kullanıcının detayları")
    p_show.add_argument("user_id", type=int)
    p_show.set_defaults(func=cmd_show)


async def _fetch_list(sort_col: str, direction: str, limit: int):
    sql = text(f"""
        SELECT u.id, u.username, u.email, u.joined_at, u.reputation,
               (SELECT COUNT(*) FROM questions q WHERE q.user_id = u.id) AS q_count,
               (SELECT COUNT(*) FROM answers  a WHERE a.user_id = u.id) AS a_count
        FROM users u
        ORDER BY {sort_col} {direction}
        LIMIT :limit
    """)
    async with session_scope() as session:
        result = await session.execute(sql, {"limit": limit})
        return result.mappings().all()


def cmd_list(args: argparse.Namespace) -> int:
    direction = "DESC" if args.desc else "ASC"
    rows = run_async(_fetch_list(SORT_COLUMNS[args.sort], direction, args.limit))

    table = Table(title=f"Kullanıcılar (sort={args.sort} {direction})", header_style="bold cyan")
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Kullanıcı adı", style="green")
    table.add_column("E-posta")
    table.add_column("Katılım", style="magenta")
    table.add_column("İtibar", justify="right", style="yellow")
    table.add_column("Soru", justify="right")
    table.add_column("Cevap", justify="right")
    for r in rows:
        table.add_row(
            str(r["id"]), r["username"], r["email"],
            r["joined_at"].strftime("%Y-%m-%d %H:%M"),
            str(r["reputation"]), str(r["q_count"]), str(r["a_count"]),
        )
    console.print(table)
    return 0


async def _fetch_show(user_id: int):
    async with session_scope() as session:
        user_row = (await session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
        )).mappings().first()
        if user_row is None:
            return None
        counts = (await session.execute(text("""
            SELECT
              (SELECT COUNT(*) FROM questions     WHERE user_id = :id)     AS q_count,
              (SELECT COUNT(*) FROM answers       WHERE user_id = :id)     AS a_count,
              (SELECT COUNT(*) FROM user_follows  WHERE followed_id = :id) AS followers,
              (SELECT COUNT(*) FROM user_follows  WHERE follower_id = :id) AS following,
              (SELECT COUNT(*) FROM tag_follows   WHERE user_id = :id)     AS followed_tags
        """), {"id": user_id})).mappings().first()
        return user_row, counts


def cmd_show(args: argparse.Namespace) -> int:
    result = run_async(_fetch_show(args.user_id))
    if result is None:
        console.print(f"[red]Kullanıcı bulunamadı: {args.user_id}[/red]")
        return 1
    user, counts = result

    table = Table(title=f"Kullanıcı #{user['id']}", show_header=False, header_style="bold cyan")
    table.add_column("Alan", style="bold")
    table.add_column("Değer")
    table.add_row("Kullanıcı adı", user["username"])
    table.add_row("E-posta", user["email"])
    table.add_row("Bio", user["bio"] or "—")
    table.add_row("Katılım", user["joined_at"].strftime("%Y-%m-%d %H:%M"))
    table.add_row("İtibar", str(user["reputation"]))
    table.add_row("Soru sayısı", str(counts["q_count"]))
    table.add_row("Cevap sayısı", str(counts["a_count"]))
    table.add_row("Takipçi", str(counts["followers"]))
    table.add_row("Takip ettiği kişi", str(counts["following"]))
    table.add_row("Takip ettiği etiket", str(counts["followed_tags"]))
    console.print(table)
    return 0
