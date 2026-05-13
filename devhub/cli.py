"""DevHub admin CLI giriş noktası."""
from __future__ import annotations

import argparse
import sys

from .commands import questions, seed_cmd, serve, stats, tags, users


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devhub",
        description="DevHub admin CLI — kullanıcı, soru, etiket ve istatistik yönetimi",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    users.add_parser(sub)
    questions.add_parser(sub)
    tags.add_parser(sub)
    stats.add_parser(sub)
    seed_cmd.add_parser(sub)
    serve.add_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
