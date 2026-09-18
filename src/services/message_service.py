"""消息业务服务。"""
import uuid
from typing import Optional

from fastapi import WebSocket

from src.constants.enums import MessageType
from src.connection.manager import ConnectionManager
from src.core.logger import logger
from src.schemas.message import (
    BaseMessage,
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

    async def dispatch(
        self, data: dict, client_id: str
    ) -> Optional[dict]:
        """解析消息并分发到对应业务处理。

        Args:
            data: 已解析的 JSON 消息字典。
            client_id: 发送方客户端 ID。

        Returns:
            需要回传给发送者的响应字典，广播/房间消息返回 None。

        Raises:
            ValueError: 消息格式校验失败或消息类型未知。
        """
        base = BaseMessage.model_validate(data)

        if base.type == MessageType.ECHO:
            return await self._handle_echo(data, client_id)
        elif base.type == MessageType.BROADCAST:
            return await self._handle_broadcast(data, client_id)
        elif base.type == MessageType.CHAT:
            return await self._handle_chat(data, client_id)
        elif base.type == MessageType.PING:
            return (await self._ping()).model_dump()
        else:
            raise ValueError(f"未知的消息类型: {base.type}")

    async def _handle_echo(
        self, data: dict, client_id: str
    ) -> dict:
        """回显：将消息原样返回给发送者。"""
        message = EchoMessage.model_validate(data)
        logger.debug(f"[Echo] 客户端 {client_id}: {message.content}")
        return EchoMessage(content=message.content).model_dump()

    async def _handle_broadcast(
        self, data: dict, client_id: str
    ) -> None:
        """广播：将消息转发给所有已连接客户端（含发送者）。"""
        message = BroadcastMessage.model_validate(data)
        logger.info(f"[Broadcast] 客户端 {client_id}: {message.content}")
        response = BroadcastMessage(
            content=message.content, sender=client_id
        )
        await self.manager.broadcast(response.model_dump_json())

    async def _handle_chat(
        self, data: dict, client_id: str
    ) -> None:
        """房间聊天：自动加入房间并转发给同房间其他成员。"""
        message = ChatMessage.model_validate(data)
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

    async def _ping(self) -> PongMessage:
        """心跳：返回 Pong 响应。"""
        return PongMessage()

    def health(self) -> dict[str, int | str]:
        """返回服务健康状态。"""
        return {
            "status": "healthy",
            "active_connections": self.manager.get_active_count(),
            "rooms": len(self.manager.rooms),
        }


message_service = MessageService()
