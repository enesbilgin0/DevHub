"""Kullanıcı yönetim alt komutları."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from ..db import connect

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


def cmd_list(args: argparse.Namespace) -> int:
    col = SORT_COLUMNS[args.sort]
    direction = "DESC" if args.desc else "ASC"
    sql = f"""
        SELECT u.id, u.username, u.email, u.joined_at, u.reputation,
               (SELECT COUNT(*) FROM questions q WHERE q.user_id = u.id) AS q_count,
               (SELECT COUNT(*) FROM answers a  WHERE a.user_id = u.id) AS a_count
        FROM users u
        ORDER BY {col} {direction}
        LIMIT ?
    """
    with connect() as conn:
        rows = conn.execute(sql, (args.limit,)).fetchall()

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
            str(r["id"]), r["username"], r["email"], r["joined_at"],
            str(r["reputation"]), str(r["q_count"]), str(r["a_count"]),
        )
    console.print(table)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (args.user_id,)).fetchone()
        if user is None:
            console.print(f"[red]Kullanıcı bulunamadı: {args.user_id}[/red]")
            return 1
        q_count = conn.execute(
            "SELECT COUNT(*) FROM questions WHERE user_id = ?", (args.user_id,)
        ).fetchone()[0]
        a_count = conn.execute(
            "SELECT COUNT(*) FROM answers WHERE user_id = ?", (args.user_id,)
        ).fetchone()[0]
        followers = conn.execute(
            "SELECT COUNT(*) FROM user_follows WHERE followed_id = ?", (args.user_id,)
        ).fetchone()[0]
        following = conn.execute(
            "SELECT COUNT(*) FROM user_follows WHERE follower_id = ?", (args.user_id,)
        ).fetchone()[0]
        followed_tags = conn.execute(
            "SELECT COUNT(*) FROM tag_follows WHERE user_id = ?", (args.user_id,)
        ).fetchone()[0]

    table = Table(title=f"Kullanıcı #{user['id']}", show_header=False, header_style="bold cyan")
    table.add_column("Alan", style="bold")
    table.add_column("Değer")
    table.add_row("Kullanıcı adı", user["username"])
    table.add_row("E-posta", user["email"])
    table.add_row("Bio", user["bio"] or "—")
    table.add_row("Katılım", user["joined_at"])
    table.add_row("İtibar", str(user["reputation"]))
    table.add_row("Soru sayısı", str(q_count))
    table.add_row("Cevap sayısı", str(a_count))
    table.add_row("Takipçi", str(followers))
    table.add_row("Takip ettiği kişi", str(following))
    table.add_row("Takip ettiği etiket", str(followed_tags))
    console.print(table)
    return 0
