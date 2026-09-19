"""WebSocket 消息路由。

包含 WebSocket 通信端点和连接管理 HTTP 接口。

Endpoints:
    WS  /channel:        WebSocket 实时通信主端点
    GET /ws/status:      服务状态概览
    GET /ws/connections:  在线连接列表
    GET /ws/rooms:        房间列表及成员信息
"""
from fastapi import APIRouter, Request, WebSocket

from src.services.message_service import MessageService

router = APIRouter(tags=["套接字消息"])


def _get_service(request: Request) -> MessageService:
    """从 app.state 获取已注入的 MessageService 实例。"""
    return request.app.state.message_service


# ---- WebSocket 通信端点 ------------------------------------------------

@router.websocket("/channel")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 实时消息频道。"""
    service: MessageService = websocket.app.state.message_service
    await service.handle_connection(websocket)


# ---- HTTP 管理接口（出现在 Swagger 文档中）-----------------------------

@router.get("/status", summary="WebSocket 服务状态概览")
async def status(request: Request) -> dict[str, int | str]:
    """查询 WebSocket 服务状态概览。

    包含在线连接数和活跃房间数。
    """
    return _get_service(request).status()


@router.get("/connections", summary="在线连接的客户端 ID 列表")
async def connections(request: Request) -> dict[str, int | list[str]]:
    """查询 WebSocket 当前所有在线连接的客户端 ID 列表。"""
    return _get_service(request).get_connections()


@router.get("/rooms", summary="活跃房间及其成员列表")
async def rooms(request: Request) -> dict[str, int | dict[str, list[str]]]:
    """查询 WebSocket 所有活跃房间及其成员列表。"""
    return _get_service(request).get_rooms()
