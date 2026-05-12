"""Veri analiz scripti — rich tabloları, opsiyonel CSV export.

Kullanım örnekleri:
    python -m scripts.analyze                       # tüm raporlar terminale
    python -m scripts.analyze --report top-questions
    python -m scripts.analyze --csv exports/        # tüm raporları CSV'ye yaz
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Paketi script olarak çalıştırırken proje kökünü importable kılalım.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from devhub import analytics  # noqa: E402
from devhub.db import connect  # noqa: E402

console = Console()


def _print(title: str, headers: list[str], rows: list[tuple]) -> None:
    table = Table(title=title, header_style="bold cyan")
    for h in headers:
        table.add_column(h)
    if not rows:
        console.print(f"[yellow]{title}: kayıt yok.[/yellow]")
        return
    for row in rows:
        table.add_row(*[str(c) if c is not None else "—" for c in row])
    console.print(table)
    console.print()


def _write_csv(out_dir: Path, name: str, headers: list[str], rows: list[tuple]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevHub veri analizi")
    parser.add_argument(
        "--report",
        choices=list(analytics.REPORTS.keys()),
        help="Sadece tek bir raporu çalıştır",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Belirtilen dizine CSV dosyaları yaz (terminale yazmaz)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Liste raporları için varsayılan limit")
    args = parser.parse_args(argv)

    selected = (
        {args.report: analytics.REPORTS[args.report]}
        if args.report
        else analytics.REPORTS
    )

    with connect() as conn:
        for name, (title, fn) in selected.items():
            try:
                headers, rows = fn(conn, args.limit) if _accepts_limit(fn) else fn(conn)
            except TypeError:
                headers, rows = fn(conn)
            if args.csv:
                path = _write_csv(args.csv, name, headers, rows)
                console.print(f"[green]✓[/green] {title} → {path}")
            else:
                _print(title, headers, rows)
    return 0


def _accepts_limit(fn) -> bool:
    import inspect
    params = inspect.signature(fn).parameters
    return "limit" in params


if __name__ == "__main__":
    sys.exit(main())
