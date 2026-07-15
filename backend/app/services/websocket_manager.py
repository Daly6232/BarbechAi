import json
import asyncio
from collections import defaultdict

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    def __init__(self):
        self.connections = defaultdict(list)
        self.main_loop = None  # set once at FastAPI startup, see main.py lifespan

    def bind_loop(self, loop):
        """Call this once from the main event loop at app startup."""
        self.main_loop = loop

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

    def push_from_thread(self, session_id: str, data: dict):
        """Safe to call from a background OS thread (e.g. enrichment workers).

        asyncio.run() from a worker thread would spin up a brand-new event loop
        and try to operate on a WebSocket object that belongs to the *main*
        uvicorn loop — ASGI transports aren't safe to touch across loops, so
        that silently failed or dropped messages. run_coroutine_threadsafe
        schedules the coroutine back onto the actual loop that owns the socket.
        """
        if not self.main_loop:
            logger.warning("WebSocketManager.push_from_thread called before bind_loop() — dropping message")
            return
        try:
            asyncio.run_coroutine_threadsafe(self.send_update(session_id, data), self.main_loop)
        except Exception as e:
            logger.warning(f"push_from_thread failed: {e}")


manager = WebSocketManager()
