"""WebSocket 连接管理接口（HTTP REST）。

提供 WebSocket 连接状态、房间信息等查询能力，
便于运维监控和调试。这些接口会出现在 Swagger 文档中。

Endpoints:
    GET /ws/status: WebSocket 服务状态概览
    GET /ws/connections: 当前在线连接列表
    GET /ws/rooms: 房间列表及成员信息
"""
from fastapi import APIRouter

from src.services import message_service

router = APIRouter(prefix="/ws", tags=["WebSocket 管理"])


@router.get("/status")
async def ws_status() -> dict[str, int | str]:
    """返回 WebSocket 服务状态概览。

    包含在线连接数和活跃房间数。
    """
    return message_service.health()


@router.get("/connections")
async def ws_connections() -> dict[str, int | list[str]]:
    """返回当前所有在线连接的客户端 ID 列表。"""
    return message_service.get_connections()


@router.get("/rooms")
async def ws_rooms() -> dict[str, int | dict[str, list[str]]]:
    """返回所有活跃房间及其成员列表。"""
    return message_service.get_rooms()
