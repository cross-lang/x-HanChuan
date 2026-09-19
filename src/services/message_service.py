"""消息业务服务。

提供 WebSocket 消息的业务处理能力，包括：
- 注册表式消息分发（替代 if/elif 链）
- 速率限制 & 消息大小校验（委托 ConnectionManager）
- 统一的接收/分发日志
"""
import json
import uuid
from typing import Callable, Coroutine, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from src.connection.manager import ConnectionManager
from src.constants.enums import MessageType
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

# 类型别名：消息处理函数签名
MessageHandler = Callable[[dict, str], Coroutine[Any, Any, Optional[dict]]]


class MessageService:
    """处理 WebSocket 消息和连接状态相关业务。

    Args:
        manager: 连接管理器实例（依赖注入）
    """

    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager

        # ------------------------------------------------------------------
        # 消息处理注册表：新增消息类型只需在此添加一行
        # ------------------------------------------------------------------
        self._handlers: dict[MessageType, MessageHandler] = {
            MessageType.ECHO: self._handle_echo,
            MessageType.BROADCAST: self._handle_broadcast,
            MessageType.CHAT: self._handle_chat,
            MessageType.PING: self._handle_ping,
        }

    # ==================================================================
    # 连接生命周期
    # ==================================================================

    async def handle_connection(self, websocket: WebSocket) -> None:
        """管理 WebSocket 连接的完整生命周期。

        包括建立连接、发送确认、接收消息循环、异常处理和断开清理。

        Args:
            websocket: WebSocket 连接对象
        """
        client_id = uuid.uuid4().hex[:12]
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

    # ==================================================================
    # 消息解析与分发
    # ==================================================================

    async def handle_raw_message(
        self, websocket: WebSocket, client_id: str, raw: str
    ) -> None:
        """校验 → 限流 → 解析 → 分发，错误时回写 ErrorMessage。

        Args:
            websocket: WebSocket 连接对象
            client_id: 发送方客户端 ID
            raw: 原始文本消息
        """
        # 1. 消息大小校验
        if not self.manager.check_message_size(raw):
            await self.send_error(
                websocket,
                f"消息超过大小上限（{self.manager.max_message_bytes} 字节）",
            )
            return

        # 2. 速率限制
        if not self.manager.check_rate_limit(client_id):
            await self.send_error(websocket, "消息发送过于频繁，请稍后重试")
            return

        # 3. JSON 解析
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            await self.send_error(websocket, "无效的 JSON 格式")
            return

        # 4. 统一接收日志
        msg_type = data.get("type", "unknown")
        logger.info(f"[消息接收] 客户端 {client_id} | 类型={msg_type} | 原始数据={raw}")

        # 5. 业务分发
        try:
            result = await self.dispatch(data, client_id)
        except ValueError as error:
            await self.send_error(websocket, str(error))
            return

        if result is not None:
            await websocket.send_json(result)

    async def dispatch(self, data: dict, client_id: str) -> Optional[dict]:
        """通过注册表解析消息并分发到对应业务处理。

        Args:
            data: 已解析的 JSON 消息字典。
            client_id: 发送方客户端 ID。

        Returns:
            需要回传给发送者的响应字典，广播/房间消息返回 None。

        Raises:
            ValueError: 消息格式校验失败或消息类型未知。
        """
        base = BaseMessage.model_validate(data)
        handler = self._handlers.get(base.type)

        if handler is None:
            raise ValueError(f"未知的消息类型: {base.type}")

        return await handler(data, client_id)

    # ==================================================================
    # 消息处理器
    # ==================================================================

    async def _handle_echo(self, data: dict, client_id: str) -> dict:
        """回显：将消息原样返回给发送者。"""
        message = EchoMessage.model_validate(data)
        logger.debug(f"[Echo] 客户端 {client_id}: {message.content}")
        return EchoMessage(content=message.content).model_dump()

    async def _handle_broadcast(self, data: dict, client_id: str) -> None:
        """广播：将消息转发给所有已连接客户端（排除发送者）。"""
        message = BroadcastMessage.model_validate(data)
        logger.info(f"[Broadcast] 客户端 {client_id}: {message.content}")
        response = BroadcastMessage(content=message.content, sender=client_id)
        await self.manager.broadcast(response.model_dump_json(), exclude=client_id)

    async def _handle_chat(self, data: dict, client_id: str) -> None:
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

    async def _handle_ping(self, data: dict, client_id: str) -> dict:
        """心跳：返回 Pong 响应。"""
        return PongMessage().model_dump()

    # ==================================================================
    # 查询接口
    # ==================================================================

    def status(self) -> dict[str, int | str]:
        """返回服务健康状态。"""
        return {
            "status": "healthy",
            "active_connections": self.manager.get_active_count(),
            "rooms": len(self.manager.rooms),
        }

    def get_connections(self) -> dict[str, int | list[str]]:
        """返回当前在线连接信息。"""
        return {
            "count": self.manager.get_active_count(),
            "client_ids": list(self.manager.active_connections.keys()),
        }

    def get_rooms(self) -> dict[str, int | dict[str, list[str]]]:
        """返回所有活跃房间及其成员信息。"""
        rooms = {
            room_id: list(members)
            for room_id, members in self.manager.rooms.items()
        }
        return {
            "count": len(rooms),
            "rooms": rooms,
        }

    # ==================================================================
    # 工具方法
    # ==================================================================

    @staticmethod
    async def send_error(websocket: WebSocket, msg: str) -> None:
        """发送结构化错误消息。"""
        await websocket.send_json(ErrorMessage(message=msg).model_dump())
