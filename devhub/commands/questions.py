"""Soru yönetim alt komutları."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table
from sqlalchemy import text

from ..db import session_scope
from . import run_async

console = Console()

SORT_COLUMNS = {
    "created": "q.created_at",
    "views": "q.view_count",
    "votes": "vote_score",
    "answers": "answer_count",
    "id": "q.id",
}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("questions", help="Soru işlemleri")
    sub = p.add_subparsers(dest="questions_action", required=True)

    p_list = sub.add_parser("list", help="Soruları listele")
    p_list.add_argument("--tag", help="Belirli bir etiketle filtrele")
    p_list.add_argument("--sort", choices=SORT_COLUMNS.keys(), default="created")
    p_list.add_argument("--desc", action="store_true")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Bir sorunun detayını göster")
    p_show.add_argument("question_id", type=int)
    p_show.set_defaults(func=cmd_show)

    p_del = sub.add_parser("delete", help="Bir soruyu sil")
    p_del.add_argument("question_id", type=int)
    p_del.add_argument("--yes", action="store_true", help="Onay sormadan sil")
    p_del.set_defaults(func=cmd_delete)


async def _fetch_list(sort_col: str, direction: str, limit: int, tag: str | None):
    where = ""
    params: dict = {"limit": limit}
    if tag:
        where = """
            WHERE q.id IN (
                SELECT qt.question_id FROM question_tags qt
                JOIN tags t ON t.id = qt.tag_id
                WHERE t.name = :tag
            )
        """
        params["tag"] = tag

    sql = text(f"""
        SELECT q.id, q.title, q.created_at, q.view_count,
               u.username,
               COALESCE(SUM(CASE WHEN v.target_type = 'question' THEN v.value END), 0) AS vote_score,
               (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) AS answer_count,
               (SELECT string_agg(t.name, ', ' ORDER BY t.name)
                  FROM question_tags qt JOIN tags t ON t.id = qt.tag_id
                  WHERE qt.question_id = q.id) AS tags
        FROM questions q
        JOIN users u ON u.id = q.user_id
        LEFT JOIN votes v ON v.target_type = 'question' AND v.target_id = q.id
        {where}
        GROUP BY q.id, u.username
        ORDER BY {sort_col} {direction}
        LIMIT :limit
    """)
    async with session_scope() as session:
        result = await session.execute(sql, params)
        return result.mappings().all()


def cmd_list(args: argparse.Namespace) -> int:
    direction = "DESC" if args.desc else "ASC"
    rows = run_async(_fetch_list(SORT_COLUMNS[args.sort], direction, args.limit, args.tag))

    title = "Sorular"
    if args.tag:
        title += f" [#{args.tag}]"
    table = Table(title=f"{title} (sort={args.sort} {direction})", header_style="bold cyan")
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Başlık", style="green")
    table.add_column("Yazar")
    table.add_column("Etiketler", style="blue")
    table.add_column("Oy", justify="right", style="yellow")
    table.add_column("Cevap", justify="right")
    table.add_column("Görüntülenme", justify="right")
    table.add_column("Tarih", style="magenta")
    for r in rows:
        title_text = r["title"] if len(r["title"]) <= 60 else r["title"][:57] + "..."
        table.add_row(
            str(r["id"]), title_text, r["username"], r["tags"] or "",
            str(r["vote_score"]), str(r["answer_count"]),
            str(r["view_count"]), r["created_at"].strftime("%Y-%m-%d %H:%M"),
        )
    console.print(table)
    return 0


async def _fetch_show(qid: int):
    async with session_scope() as session:
        q = (await session.execute(
            text("""SELECT q.*, u.username FROM questions q
                    JOIN users u ON u.id = q.user_id WHERE q.id = :id"""),
            {"id": qid},
        )).mappings().first()
        if q is None:
            return None
        tags = [r[0] for r in (await session.execute(
            text("""SELECT t.name FROM tags t JOIN question_tags qt ON qt.tag_id = t.id
                    WHERE qt.question_id = :id ORDER BY t.name"""),
            {"id": qid},
        )).all()]
        meta = (await session.execute(text("""
            SELECT
              (SELECT COUNT(*) FROM answers WHERE question_id = :id) AS answer_count,
              COALESCE(
                (SELECT SUM(value) FROM votes WHERE target_type='question' AND target_id = :id),
                0
              ) AS vote_score
        """), {"id": qid})).mappings().first()
        return q, tags, meta


def cmd_show(args: argparse.Namespace) -> int:
    result = run_async(_fetch_show(args.question_id))
    if result is None:
        console.print(f"[red]Soru bulunamadı: {args.question_id}[/red]")
        return 1
    q, tags, meta = result

    console.print(f"[bold green]#{q['id']}[/bold green] [bold]{q['title']}[/bold]")
    console.print(
        f"  yazar: [cyan]{q['username']}[/cyan]  "
        f"tarih: [magenta]{q['created_at'].strftime('%Y-%m-%d %H:%M')}[/magenta]"
    )
    console.print(f"  etiketler: [blue]{', '.join(tags) or '—'}[/blue]")
    console.print(
        f"  oy: [yellow]{meta['vote_score']}[/yellow]  "
        f"cevap: {meta['answer_count']}  görüntülenme: {q['view_count']}"
    )
    console.print()
    console.print(q["body"])
    return 0


async def _fetch_title(qid: int) -> str | None:
    async with session_scope() as session:
        row = (await session.execute(
            text("SELECT title FROM questions WHERE id = :id"), {"id": qid}
        )).first()
        return row[0] if row else None


async def _delete(qid: int) -> int:
    async with session_scope() as session:
        result = await session.execute(
            text("DELETE FROM questions WHERE id = :id"), {"id": qid}
        )
        return result.rowcount  # type: ignore[attr-defined]


def cmd_delete(args: argparse.Namespace) -> int:
    title = run_async(_fetch_title(args.question_id))
    if title is None:
        console.print(f"[red]Soru bulunamadı: {args.question_id}[/red]")
        return 1
    if not args.yes:
        console.print(f"Silinecek: [bold]{title}[/bold]")
        confirm = input("Onaylıyor musun? (y/N) ").strip().lower()
        if confirm != "y":
            console.print("[yellow]İptal edildi.[/yellow]")
            return 0
    run_async(_delete(args.question_id))
    console.print(f"[green]Soru #{args.question_id} silindi.[/green]")
    return 0
