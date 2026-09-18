"""
消息数据模型

定义 WebSocket 通信中使用的所有消息类型，基于 Pydantic v2 实现数据校验。
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MessageType(str, Enum):
    """消息类型枚举

    每种类型对应一种 WebSocket 通信场景：
    - ECHO: 回显消息（服务器原样返回）
    - BROADCAST: 广播消息（转发给所有已连接客户端）
    - CHAT: 房间聊天消息（转发给同一房间内的其他客户端）
    - PING / PONG: 心跳检测
    - ERROR: 错误消息
    - CONNECTED: 连接确认消息
    """
    ECHO = "echo"
    BROADCAST = "broadcast"
    CHAT = "chat"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"


class BaseMessage(BaseModel):
    """基础消息模型

    所有消息类型均继承此模型，包含消息类型和时间戳字段。
    """
    type: MessageType
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class EchoMessage(BaseMessage):
    """回显消息

    用于演示最基础的 WebSocket 通信：客户端发送消息，服务器原样返回。
    """
    type: MessageType = MessageType.ECHO
    content: str


class BroadcastMessage(BaseMessage):
    """广播消息

    用于演示一对多通信：客户端发送消息，服务器转发给所有已连接的客户端。
    """
    type: MessageType = MessageType.BROADCAST
    content: str
    sender: Optional[str] = None


class ChatMessage(BaseMessage):
    """房间聊天消息

    用于演示房间（Room）机制：客户端加入指定房间后，消息仅转发给同一房间内的其他成员。
    """
    type: MessageType = MessageType.CHAT
    content: str
    room_id: str
    sender: Optional[str] = None


class ErrorMessage(BaseMessage):
    """错误消息

    服务器在处理请求出错时返回此消息。
    """
    type: MessageType = MessageType.ERROR
    message: str
    code: Optional[str] = None


class ConnectedMessage(BaseMessage):
    """连接成功消息

    客户端成功连接后，服务器返回此消息确认连接已建立。
    """
    type: MessageType = MessageType.CONNECTED
    message: str
    client_id: str