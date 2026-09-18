"""
WebSocket 连接管理器

负责管理所有 WebSocket 连接的生命周期，提供以下核心能力：
- 连接注册与注销
- 点对点消息发送
- 全局广播
- 房间（Room）管理与房间内广播
"""
from typing import Dict, Set, Optional
from fastapi import WebSocket

from ..core.logger import logger


class ConnectionManager:
    """WebSocket 连接管理器

    维护所有活跃连接和房间映射关系，是服务器消息分发的核心组件。

    Attributes:
        active_connections: 已连接的客户端映射（client_id → WebSocket）
        rooms: 房间映射（room_id → 客户端 ID 集合）
    """

    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """注册新连接

        Args:
            websocket: WebSocket 连接对象
            client_id: 客户端唯一标识
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"客户端 {client_id} 已连接，当前在线: {self.get_active_count()}")

    async def disconnect(self, client_id: str) -> None:
        """注销连接，并从所有房间中移除

        Args:
            client_id: 客户端唯一标识
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端 {client_id} 已断开，当前在线: {self.get_active_count()}")

        # 从所有房间中移除该客户端
        empty_rooms: list[str] = []
        for room_id, members in self.rooms.items():
            members.discard(client_id)
            if not members:
                empty_rooms.append(room_id)
        for room_id in empty_rooms:
            del self.rooms[room_id]

    async def send_personal(self, message: str, client_id: str) -> None:
        """向指定客户端发送消息

        Args:
            message: 消息内容（JSON 字符串）
            client_id: 目标客户端 ID
        """
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"发送消息给 {client_id} 失败: {e}")

    async def broadcast(self, message: str, exclude: Optional[str] = None) -> None:
        """向所有已连接客户端广播消息

        Args:
            message: 消息内容（JSON 字符串）
            exclude: 排除的客户端 ID（通常排除发送者自身）
        """
        for client_id, ws in self.active_connections.items():
            if client_id == exclude:
                continue
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"广播消息给 {client_id} 失败: {e}")

    async def join_room(self, room_id: str, client_id: str) -> None:
        """将客户端加入指定房间

        Args:
            room_id: 房间 ID
            client_id: 客户端 ID
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(client_id)
        logger.info(f"客户端 {client_id} 加入房间 {room_id}，房间人数: {len(self.rooms[room_id])}")

    async def leave_room(self, room_id: str, client_id: str) -> None:
        """将客户端移出指定房间

        Args:
            room_id: 房间 ID
            client_id: 客户端 ID
        """
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].discard(client_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            logger.info(f"客户端 {client_id} 离开房间 {room_id}")

    async def broadcast_to_room(
        self, room_id: str, message: str, exclude: Optional[str] = None
    ) -> None:
        """向房间内所有成员广播消息

        Args:
            room_id: 房间 ID
            message: 消息内容（JSON 字符串）
            exclude: 排除的客户端 ID（通常排除发送者自身）
        """
        members = self.rooms.get(room_id, set())
        for client_id in members:
            if client_id == exclude:
                continue
            await self.send_personal(message, client_id)

    def get_active_count(self) -> int:
        """获取当前在线客户端数量"""
        return len(self.active_connections)

    def get_room_count(self, room_id: str) -> int:
        """获取指定房间的成员数量"""
        return len(self.rooms.get(room_id, set()))