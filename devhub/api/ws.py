"""WebSocket connection manager — kullanıcıya göre çoklu bağlantı tutar."""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._conns: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._conns.setdefault(user_id, set()).add(ws)

    async def disconnect(self, user_id: int, ws: WebSocket) -> None:
        async with self._lock:
            if user_id in self._conns:
                self._conns[user_id].discard(ws)
                if not self._conns[user_id]:
                    del self._conns[user_id]

    async def send_to_user(self, user_id: int, event: dict[str, Any]) -> int:
        """user_id'ye event yayar. Düşen bağlantılar temizlenir. Yollanan sayıyı döner."""
        async with self._lock:
            targets = list(self._conns.get(user_id, ()))
        dead: list[WebSocket] = []
        sent = 0
        for ws in targets:
            try:
                await ws.send_json(event)
                sent += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)
        return sent

    def is_connected(self, user_id: int) -> bool:
        return user_id in self._conns and len(self._conns[user_id]) > 0


manager = ConnectionManager()
