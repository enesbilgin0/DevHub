"""Etiket yönetim alt komutları."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ..db import session_scope
from . import run_async

console = Console()


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("tags", help="Etiket işlemleri")
    sub = p.add_subparsers(dest="tags_action", required=True)

    p_list = sub.add_parser("list", help="Etiketleri listele")
    p_list.add_argument("--sort", choices=("name", "questions", "followers"), default="questions")
    p_list.add_argument("--limit", type=int, default=30)
    p_list.set_defaults(func=cmd_list)

    p_add = sub.add_parser("add", help="Yeni etiket ekle")
    p_add.add_argument("name")
    p_add.add_argument("--description", default=None)
    p_add.set_defaults(func=cmd_add)

    p_del = sub.add_parser("delete", help="Etiketi sil")
    p_del.add_argument("name")
    p_del.set_defaults(func=cmd_delete)


async def _fetch_list(sort_sql: str, limit: int):
    sql = text(f"""
        SELECT t.id, t.name, t.description,
               (SELECT COUNT(*) FROM question_tags qt WHERE qt.tag_id = t.id) AS question_count,
               (SELECT COUNT(*) FROM tag_follows  tf WHERE tf.tag_id = t.id) AS follower_count
        FROM tags t
        ORDER BY {sort_sql}
        LIMIT :limit
    """)
    async with session_scope() as session:
        result = await session.execute(sql, {"limit": limit})
        return result.mappings().all()


def cmd_list(args: argparse.Namespace) -> int:
    sort_sql = {
        "name": "t.name ASC",
        "questions": "question_count DESC",
        "followers": "follower_count DESC",
    }[args.sort]
    rows = run_async(_fetch_list(sort_sql, args.limit))

    table = Table(title=f"Etiketler (sort={args.sort})", header_style="bold cyan")
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Ad", style="blue")
    table.add_column("Açıklama")
    table.add_column("Soru", justify="right", style="yellow")
    table.add_column("Takipçi", justify="right", style="green")
    for r in rows:
        table.add_row(
            str(r["id"]), r["name"], r["description"] or "",
            str(r["question_count"]), str(r["follower_count"]),
        )
    console.print(table)
    return 0


async def _add(name: str, description: str | None) -> bool:
    try:
        async with session_scope() as session:
            await session.execute(
                text("INSERT INTO tags (name, description) VALUES (:name, :description)"),
                {"name": name, "description": description},
            )
        return True
    except IntegrityError:
        return False


def cmd_add(args: argparse.Namespace) -> int:
    if not run_async(_add(args.name, args.description)):
        console.print(f"[red]Etiket zaten mevcut: {args.name}[/red]")
        return 1
    console.print(f"[green]Etiket eklendi: {args.name}[/green]")
    return 0


async def _delete(name: str) -> int:
    async with session_scope() as session:
        result = await session.execute(
            text("DELETE FROM tags WHERE name = :name"), {"name": name}
        )
        return result.rowcount


def cmd_delete(args: argparse.Namespace) -> int:
    if run_async(_delete(args.name)) == 0:
        console.print(f"[red]Etiket bulunamadı: {args.name}[/red]")
        return 1
    console.print(f"[green]Etiket silindi: {args.name}[/green]")
    return 0
