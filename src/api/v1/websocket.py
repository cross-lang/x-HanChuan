"""WebSocket API 路由。"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...constants.enums import MessageType
from ...core.logger import logger
from ...schemas.message import (
    BaseMessage,
    BroadcastMessage,
    ChatMessage,
    EchoMessage,
    ErrorMessage,
)
from ...services import message_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """接收和校验 WebSocket 消息，并交给业务服务处理。"""
    connected = await message_service.connect(websocket)
    client_id = connected.client_id
    await websocket.send_json(connected.model_dump())

    try:
        while True:
            raw = await websocket.receive_text()
            await _dispatch(websocket, client_id, raw)
    except WebSocketDisconnect:
        logger.info(f"客户端 {client_id} 主动断开")
    except Exception as error:
        logger.error(f"客户端 {client_id} 异常: {error}")
    finally:
        await message_service.disconnect(client_id)


async def _dispatch(
    websocket: WebSocket, client_id: str, raw: str
) -> None:
    """解析并校验消息，然后调用对应业务服务。"""
    try:
        data = json.loads(raw)
        base = BaseMessage.model_validate(data)
    except (json.JSONDecodeError, TypeError, ValueError):
        await _send_error(websocket, "消息格式校验失败")
        return

    try:
        if base.type == MessageType.ECHO:
            message = EchoMessage.model_validate(data)
            response = await message_service.echo(message, client_id)
            await websocket.send_json(response.model_dump())
        elif base.type == MessageType.BROADCAST:
            message = BroadcastMessage.model_validate(data)
            await message_service.broadcast(message, client_id)
        elif base.type == MessageType.CHAT:
            message = ChatMessage.model_validate(data)
            await message_service.chat(message, client_id)
        elif base.type == MessageType.PING:
            response = await message_service.ping()
            await websocket.send_json(response.model_dump())
        else:
            await _send_error(websocket, f"未知的消息类型: {base.type}")
    except ValueError:
        await _send_error(websocket, "消息格式校验失败")


async def _send_error(websocket: WebSocket, message: str) -> None:
    """发送结构化错误消息。"""
    response = ErrorMessage(message=message)
    await websocket.send_json(response.model_dump())
