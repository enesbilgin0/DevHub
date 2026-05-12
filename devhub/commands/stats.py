"""Genel istatistik alt komutu."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from ..db import connect

console = Console()


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("stats", help="Platform geneli istatistikler")
    p.set_defaults(func=cmd_stats)


def cmd_stats(args: argparse.Namespace) -> int:
    with connect() as conn:
        counts = {
            "Kullanıcılar":  conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "Sorular":       conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0],
            "Cevaplar":      conn.execute("SELECT COUNT(*) FROM answers").fetchone()[0],
            "Etiketler":     conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0],
            "Oylar":         conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0],
            "Kullanıcı takipleri": conn.execute("SELECT COUNT(*) FROM user_follows").fetchone()[0],
            "Etiket takipleri":    conn.execute("SELECT COUNT(*) FROM tag_follows").fetchone()[0],
            "Kabul edilmiş cevap": conn.execute(
                "SELECT COUNT(*) FROM answers WHERE is_accepted = 1"
            ).fetchone()[0],
        }

    table = Table(title="DevHub — Genel İstatistikler", header_style="bold cyan")
    table.add_column("Metrik", style="bold")
    table.add_column("Değer", justify="right", style="yellow")
    for k, v in counts.items():
        table.add_row(k, f"{v:,}")
    console.print(table)
    return 0
