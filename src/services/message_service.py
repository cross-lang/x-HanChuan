"""消息业务服务。"""
import uuid

from fastapi import WebSocket

from ..connection.manager import ConnectionManager
from ..core.logger import logger
from ..schemas.message import (
    BroadcastMessage,
    ChatMessage,
    ConnectedMessage,
    EchoMessage,
    PongMessage,
)


class MessageService:
    """处理 WebSocket 消息和连接状态相关业务。"""

    def __init__(self) -> None:
        self.manager = ConnectionManager()

    async def connect(self, websocket: WebSocket) -> ConnectedMessage:
        """建立客户端连接并返回连接确认消息。"""
        client_id = str(uuid.uuid4())[:8]
        await self.manager.connect(websocket, client_id)
        return ConnectedMessage(message="连接已建立", client_id=client_id)

    async def disconnect(self, client_id: str) -> None:
        """断开客户端连接。"""
        await self.manager.disconnect(client_id)

    async def echo(self, message: EchoMessage, client_id: str) -> EchoMessage:
        """处理回显消息。"""
        logger.debug(f"[Echo] 客户端 {client_id}: {message.content}")
        return EchoMessage(content=message.content)

    async def broadcast(
        self, message: BroadcastMessage, client_id: str
    ) -> None:
        """向所有已连接客户端广播消息。"""
        logger.info(f"[Broadcast] 客户端 {client_id}: {message.content}")
        response = BroadcastMessage(content=message.content, sender=client_id)
        await self.manager.broadcast(response.model_dump_json())

    async def chat(self, message: ChatMessage, client_id: str) -> None:
        """加入房间并向同房间其他成员转发消息。"""
        await self.manager.join_room(message.room_id, client_id)
        logger.info(
            f"[Chat] 客户端 {client_id} → 房间 {message.room_id}: "
            f"{message.content}"
        )
        response = ChatMessage(
            content=message.content,
            room_id=message.room_id,
            sender=client_id,
        )
        await self.manager.broadcast_to_room(
            message.room_id,
            response.model_dump_json(),
            exclude=client_id,
        )

    async def ping(self) -> PongMessage:
        """处理心跳消息。"""
        return PongMessage()

    def health(self) -> dict[str, int | str]:
        """返回服务健康状态。"""
        return {
            "status": "healthy",
            "active_connections": self.manager.get_active_count(),
            "rooms": len(self.manager.rooms),
        }


message_service = MessageService()
