import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.logger import logger

router = APIRouter(tags=["WebSocket - Live Claim Status"])


class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    async def connect(self, claim_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(claim_id, []).append(websocket)

    def disconnect(self, claim_id: int, websocket: WebSocket) -> None:
        if claim_id in self.active_connections:
            if websocket in self.active_connections[claim_id]:
                self.active_connections[claim_id].remove(websocket)
            if not self.active_connections[claim_id]:
                del self.active_connections[claim_id]

    async def broadcast(self, claim_id: int, message: dict) -> None:
        for connection in self.active_connections.get(claim_id, []):
            try:
                await connection.send_json(message)
            except Exception as error:
                logger.error(f"WebSocket send failed : {str(error)}")


manager = ConnectionManager()


@router.websocket("/ws/claims/{claim_id}")
async def claim_status_socket(websocket: WebSocket, claim_id: int):
    await manager.connect(claim_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(claim_id, websocket)


# called from synchronous service functions - hands the broadcast off to
# the real event loop safely, same fix originally needed for the travel
# platform's websocket, carried forward correctly here from the start
def broadcast_claim_status_sync(claim_id: int, new_status: str) -> None:

    if manager.loop is None:
        logger.error("WebSocket broadcast skipped : event loop not yet available.")
        return

    try:
        message = {"claim_id": claim_id, "status": new_status}
        asyncio.run_coroutine_threadsafe(manager.broadcast(claim_id, message), manager.loop)
    except Exception as error:
        logger.error(f"WebSocket broadcast failed : {str(error)}")