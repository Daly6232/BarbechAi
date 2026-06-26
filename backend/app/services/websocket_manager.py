import json
from collections import defaultdict

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    def __init__(self):
        self.connections = defaultdict(list)

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
    ):
        await websocket.accept()

        self.connections[session_id].append(websocket)

        logger.info(
            f"WebSocket connected: {session_id}"
        )

    def disconnect(
        self,
        websocket: WebSocket,
        session_id: str,
    ):
        if websocket in self.connections[session_id]:
            self.connections[session_id].remove(websocket)

        if not self.connections[session_id]:
            self.connections.pop(session_id, None)

        logger.info(
            f"WebSocket disconnected: {session_id}"
        )

    async def send_update(
        self,
        session_id: str,
        data: dict,
    ):
        dead_connections = []

        for websocket in self.connections.get(session_id, []):

            try:
                await websocket.send_text(
                    json.dumps(data)
                )

            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(
                websocket,
                session_id,
            )


manager = WebSocketManager()
