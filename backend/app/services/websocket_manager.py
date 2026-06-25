from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.connections:
            self.connections[session_id].remove(websocket)

    async def send_update(self, session_id: str, data: dict):
        if session_id in self.connections:
            dead = []
            for ws in self.connections[session_id]:
                try:
                    await ws.send_text(json.dumps(data))
                except:
                    dead.append(ws)
            for ws in dead:
                self.connections[session_id].remove(ws)

manager = WebSocketManager()
