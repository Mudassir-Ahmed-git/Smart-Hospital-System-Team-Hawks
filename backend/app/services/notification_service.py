"""Real-time notifications: WebSocket fan-out + logging.
Sync route handlers run in a worker thread, so we hop back to the event loop with anyio."""
import logging
from typing import Any

from anyio import from_thread
from fastapi import WebSocket

log = logging.getLogger("notifications")


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: list[tuple[WebSocket, int | None]] = []  # (socket, hospital_id filter)

    async def connect(self, ws: WebSocket, hospital_id: int | None = None) -> None:
        await ws.accept()
        self.connections.append((ws, hospital_id))

    def disconnect(self, ws: WebSocket) -> None:
        self.connections = [(w, h) for (w, h) in self.connections if w is not ws]

    async def broadcast(self, message: dict[str, Any]) -> None:
        target = message.get("hospitalId")
        for ws, hid in list(self.connections):
            if hid is not None and target is not None and hid != target:
                continue
            try:
                await ws.send_json(message)
            except Exception:  # dead socket
                self.disconnect(ws)


manager = ConnectionManager()


def publish(event: str, **payload: Any) -> None:
    """Fire-and-forget event for connected dashboards. Never raises."""
    message = {"event": event, **payload}
    log.info("event=%s %s", event, payload)
    if not manager.connections:
        return
    try:
        from_thread.run(manager.broadcast, message)
    except Exception:  # called outside a worker thread (seed script, tests) - ignore
        pass


def notify_capacity_changed(hospital_id: int) -> None:
    publish("capacity_updated", hospitalId=hospital_id)


def notify_new_request(kind: str, request_id: str, hospital_id: int, priority: str) -> None:
    publish("new_request", kind=kind, requestId=request_id, hospitalId=hospital_id, priority=priority)


def notify_status_change(kind: str, request_id: str, status: str, hospital_id: int | None) -> None:
    publish("status_changed", kind=kind, requestId=request_id, status=status, hospitalId=hospital_id)
