"""Seed alt komutu — DB'yi sıfırlayıp Faker ile doldurur."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from ..seed import DEFAULT_ANSWERS, DEFAULT_QUESTIONS, DEFAULT_USERS, run

console = Console()


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("seed", help="DB'yi sıfırla ve sahte veri üret")
    p.add_argument("--users", type=int, default=DEFAULT_USERS)
    p.add_argument("--questions", type=int, default=DEFAULT_QUESTIONS)
    p.add_argument("--answers", type=int, default=DEFAULT_ANSWERS)
    p.add_argument("--seed", type=int, default=42, help="Rastgelelik için tohum")
    p.set_defaults(func=cmd_seed)


def cmd_seed(args: argparse.Namespace) -> int:
    console.print("[cyan]Sahte veri üretiliyor…[/cyan]")
    stats = run(
        users=args.users,
        questions=args.questions,
        answers=args.answers,
        seed=args.seed,
    )
    table = Table(title="Seed tamamlandı", header_style="bold green")
    table.add_column("Varlık", style="bold")
    table.add_column("Adet", justify="right", style="yellow")
    for k, v in stats.items():
        table.add_row(k, f"{v:,}")
    console.print(table)
    return 0
