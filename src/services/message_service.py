"""消息业务服务。"""
import json
import uuid
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from src.constants.enums import MessageType
from src.connection.manager import ConnectionManager
from src.core.logger import logger
from src.schemas.message import (
    BaseMessage,
    BroadcastMessage,
    ChatMessage,
    ConnectedMessage,
    EchoMessage,
    ErrorMessage,
    PongMessage,
)


class MessageService:
    """处理 WebSocket 消息和连接状态相关业务。"""

    def __init__(self) -> None:
        self.manager = ConnectionManager()

    async def handle_connection(self, websocket: WebSocket) -> None:
        """管理 WebSocket 连接的完整生命周期。

        包括建立连接、发送确认、接收消息循环、异常处理和断开清理。

        Args:
            websocket: WebSocket 连接对象
        """
        client_id = str(uuid.uuid4())[:8]
        await self.manager.connect(websocket, client_id)
        await websocket.send_json(
            ConnectedMessage(message="连接已建立", client_id=client_id).model_dump()
        )

        try:
            while True:
                raw = await websocket.receive_text()
                await self.handle_raw_message(websocket, client_id, raw)
        except WebSocketDisconnect:
            logger.info(f"客户端 {client_id} 主动断开")
        except Exception as error:
            logger.error(f"客户端 {client_id} 异常: {error}")
        finally:
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

    async def handle_raw_message(
        self, websocket: WebSocket, client_id: str, raw: str
    ) -> None:
        """解析原始文本并分发业务，错误时回写 ErrorMessage。

        Args:
            websocket: WebSocket 连接对象
            client_id: 发送方客户端 ID
            raw: 原始文本消息
        """
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            await self.send_error(websocket, "无效的 JSON 格式")
            return

        try:
            result = await self.dispatch(data, client_id)
        except ValueError as error:
            await self.send_error(websocket, str(error))
            return

        if result is not None:
            await websocket.send_json(result)

    @staticmethod
    async def send_error(websocket: WebSocket, msg: str) -> None:
        """发送结构化错误消息。"""
        await websocket.send_json(ErrorMessage(message=msg).model_dump())

    def get_connections(self) -> dict[str, int | list[str]]:
        """返回当前在线连接信息。"""
        return {
            "count": self.manager.get_active_count(),
            "client_ids": list(self.manager.active_connections.keys()),
        }

    def get_rooms(self) -> dict[str, int | dict[str, list[str]]]:
        """返回所有活跃房间及成员信息。"""
        rooms = {
            room_id: list(members)
            for room_id, members in self.manager.rooms.items()
        }
        return {
            "count": len(rooms),
            "rooms": rooms,
        }


message_service = MessageService()
