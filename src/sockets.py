import asyncio

from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_updates(self, data: dict):
        if not self.active_connections:
            return

        await asyncio.gather(
            *[connection.send_json(data) for connection in self.active_connections]
        )

