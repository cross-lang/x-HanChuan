"""WebSocket 路由。

包含 WebSocket 通信端点和连接管理 HTTP 接口。

Endpoints:
    WS  /channel:        WebSocket 实时通信主端点
    GET /ws/status:      服务状态概览
    GET /ws/connections:  在线连接列表
    GET /ws/rooms:        房间列表及成员信息
"""
from fastapi import APIRouter, WebSocket

from src.services import message_service

router = APIRouter(tags=["WebSocket"])


# ---- WebSocket 通信端点 ------------------------------------------------

@router.websocket("/channel")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 实时消息频道。"""
    await message_service.handle_connection(websocket)


# ---- HTTP 管理接口（出现在 Swagger 文档中）-----------------------------

@router.get("/status", tags=["WebSocket 服务状态概览"])
async def status() -> dict[str, int | str]:
    """查询 WebSocket 服务状态概览。

    包含在线连接数和活跃房间数。
    """
    return message_service.status()


@router.get("/connections", tags=["WebSocket 当前所有在线连接的客户端 ID 列表"])
async def connections() -> dict[str, int | list[str]]:
    """查询 WebSocket 当前所有在线连接的客户端 ID 列表。"""
    return message_service.get_connections()


@router.get("/rooms", tags=["所有活跃房间及其成员列表"])
async def rooms() -> dict[str, int | dict[str, list[str]]]:
    """查询 WebSocket 所有活跃房间及其成员列表。"""
    return message_service.get_rooms()
