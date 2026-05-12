"""Soru yönetim alt komutları."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from ..db import connect

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


def cmd_list(args: argparse.Namespace) -> int:
    col = SORT_COLUMNS[args.sort]
    direction = "DESC" if args.desc else "ASC"
    params: list = []
    where = ""
    if args.tag:
        where = """
            WHERE q.id IN (
                SELECT qt.question_id FROM question_tags qt
                JOIN tags t ON t.id = qt.tag_id
                WHERE t.name = ?
            )
        """
        params.append(args.tag)
    params.append(args.limit)

    sql = f"""
        SELECT q.id, q.title, q.created_at, q.view_count,
               u.username,
               COALESCE(SUM(CASE WHEN v.target_type = 'question' THEN v.value END), 0) AS vote_score,
               (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) AS answer_count,
               (SELECT GROUP_CONCAT(t.name, ', ')
                  FROM question_tags qt JOIN tags t ON t.id = qt.tag_id
                  WHERE qt.question_id = q.id) AS tags
        FROM questions q
        JOIN users u ON u.id = q.user_id
        LEFT JOIN votes v ON v.target_type = 'question' AND v.target_id = q.id
        {where}
        GROUP BY q.id
        ORDER BY {col} {direction}
        LIMIT ?
    """

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

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
            str(r["view_count"]), r["created_at"],
        )
    console.print(table)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with connect() as conn:
        q = conn.execute(
            """SELECT q.*, u.username FROM questions q
               JOIN users u ON u.id = q.user_id WHERE q.id = ?""",
            (args.question_id,),
        ).fetchone()
        if q is None:
            console.print(f"[red]Soru bulunamadı: {args.question_id}[/red]")
            return 1
        tags = [r["name"] for r in conn.execute(
            """SELECT t.name FROM tags t JOIN question_tags qt ON qt.tag_id = t.id
               WHERE qt.question_id = ? ORDER BY t.name""",
            (args.question_id,),
        ).fetchall()]
        answer_count = conn.execute(
            "SELECT COUNT(*) FROM answers WHERE question_id = ?", (args.question_id,)
        ).fetchone()[0]
        vote_score = conn.execute(
            """SELECT COALESCE(SUM(value), 0) FROM votes
               WHERE target_type='question' AND target_id = ?""",
            (args.question_id,),
        ).fetchone()[0]

    console.print(f"[bold green]#{q['id']}[/bold green] [bold]{q['title']}[/bold]")
    console.print(f"  yazar: [cyan]{q['username']}[/cyan]  tarih: [magenta]{q['created_at']}[/magenta]")
    console.print(f"  etiketler: [blue]{', '.join(tags) or '—'}[/blue]")
    console.print(f"  oy: [yellow]{vote_score}[/yellow]  cevap: {answer_count}  görüntülenme: {q['view_count']}")
    console.print()
    console.print(q["body"])
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT title FROM questions WHERE id = ?", (args.question_id,)
        ).fetchone()
        if row is None:
            console.print(f"[red]Soru bulunamadı: {args.question_id}[/red]")
            return 1
        if not args.yes:
            console.print(f"Silinecek: [bold]{row['title']}[/bold]")
            confirm = input("Onaylıyor musun? (y/N) ").strip().lower()
            if confirm != "y":
                console.print("[yellow]İptal edildi.[/yellow]")
                return 0
        conn.execute("DELETE FROM questions WHERE id = ?", (args.question_id,))
        conn.commit()
    console.print(f"[green]Soru #{args.question_id} silindi.[/green]")
    return 0
