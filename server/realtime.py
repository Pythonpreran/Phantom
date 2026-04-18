"""
PHANTOM — Real-time WebSocket Manager
Only broadcasts REAL user-generated events. No simulation.
"""

import json
from datetime import datetime
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        dead = []
        data = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    def get_active_count(self) -> int:
        return len(self.active_connections)


# Singleton
manager = ConnectionManager()


async def broadcast_real_event(log_entry: dict, ml_result: dict, db_stats: dict):
    """
    Broadcast a REAL event to all WebSocket clients.
    Called from website/attack routes when a user performs an action.
    db_stats must be freshly queried from the database.
    """
    await manager.broadcast({
        "type": "event",
        "data": log_entry,
        "stats": db_stats,
    })


# Legacy alias so existing imports don't break
async def broadcast_xyz_event(log_entry: dict, ml_result: dict):
    """Legacy wrapper — broadcasts without stats (stats fetched by admin via REST)."""
    await manager.broadcast({
        "type": "event",
        "data": log_entry,
    })
