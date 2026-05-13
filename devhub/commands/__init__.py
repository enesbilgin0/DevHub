"""CLI alt komutları için ortak yardımcılar."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable

from ..db import dispose_engine


def run_async[T](coro: Awaitable[T]) -> T:
    """Async coroutine'i çalıştır ve engine'i temiz kapat."""

    async def _runner() -> T:
        try:
            return await coro
        finally:
            await dispose_engine()

    return asyncio.run(_runner())
