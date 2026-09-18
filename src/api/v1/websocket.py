"""WebSocket API 路由。"""
from fastapi import APIRouter, WebSocket

from src.services import message_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 主端点。连接生命周期、消息处理均由 MessageService 管理。"""
    await message_service.handle_connection(websocket)
