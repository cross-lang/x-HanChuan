"""
消息数据模型

定义 WebSocket 通信中使用的所有消息类型，基于 Pydantic v2 实现数据校验。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.constants.enums import MessageType


class BaseMessage(BaseModel):
    """基础消息模型。"""

    type: MessageType
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class EchoMessage(BaseMessage):
    """回显消息。"""

    type: MessageType = MessageType.ECHO
    content: str


class BroadcastMessage(BaseMessage):
    """广播消息。"""

    type: MessageType = MessageType.BROADCAST
    content: str
    sender: Optional[str] = None


class ChatMessage(BaseMessage):
    """房间聊天消息。"""

    type: MessageType = MessageType.CHAT
    content: str
    room_id: str
    sender: Optional[str] = None


class ErrorMessage(BaseMessage):
    """错误消息。"""

    type: MessageType = MessageType.ERROR
    message: str
    code: Optional[str] = None


class ConnectedMessage(BaseMessage):
    """连接成功消息。"""

    type: MessageType = MessageType.CONNECTED
    message: str
    client_id: str


class PongMessage(BaseMessage):
    """心跳响应消息。"""

    type: MessageType = MessageType.PONG
