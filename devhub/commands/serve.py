"""`devhub serve` — uvicorn ile FastAPI'yi başlat."""
from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("serve", help="FastAPI uygulamasını uvicorn ile başlat")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--reload", action="store_true", help="Geliştirme için kod değişikliğini izle")
    p.set_defaults(func=cmd_serve)


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn  # lazily to keep CLI import cheap

    uvicorn.run(
        "devhub.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0
