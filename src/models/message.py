"""
消息数据模型

定义 WebSocket 通信中使用的所有消息类型，基于 Pydantic v2 实现数据校验。
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.constants.enums import MessageType


class BaseMessage(BaseModel):
    """基础消息模型

    所有消息类型均继承此模型，包含消息类型和时间戳字段。
    """
    type: MessageType
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class EchoMessage(BaseMessage):
    """回显消息

    客户端发送消息，服务器原样返回。
    """
    type: MessageType = MessageType.ECHO
    content: str


class BroadcastMessage(BaseMessage):
    """广播消息

    一对多通信：客户端发送消息，服务器转发给所有已连接的客户端。
    """
    type: MessageType = MessageType.BROADCAST
    content: str
    sender: Optional[str] = None


class ChatMessage(BaseMessage):
    """房间聊天消息

    房间机制：客户端加入指定房间后，消息仅转发给同一房间内的其他成员。
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


class PongMessage(BaseMessage):
    """心跳响应消息

    服务器收到 Ping 消息后返回此消息，用于连接保活和延迟测量。
    """
    type: MessageType = MessageType.PONG