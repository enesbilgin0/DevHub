"""WebSocket router — /ws bağlantısı, JWT ile auth."""
from __future__ import annotations

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from ..security import decode_token
from ..ws import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    """JWT access token'ı ile auth. `?token=<jwt>` query parametresi zorunlu.

    Server tek yönlü mesaj yayını yapar; client'tan gelen mesajlar yutulur.
    """
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid token")
        return

    await manager.connect(user_id, ws)
    try:
        while True:
            # Client'tan gelen mesajları yutar (ping/pong, heartbeat).
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id, ws)
