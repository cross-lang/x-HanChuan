"""WebSocket API 路由。"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.logger import logger
from src.schemas.message import ErrorMessage
from src.services import message_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 主端点。

    只负责连接生命周期、JSON 解析和错误回写，
    具体业务逻辑由 MessageService 处理。
    """
    connected = await message_service.connect(websocket)
    client_id = connected.client_id
    await websocket.send_json(connected.model_dump())

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_message(websocket, client_id, raw)
    except WebSocketDisconnect:
        logger.info(f"客户端 {client_id} 主动断开")
    except Exception as error:
        logger.error(f"客户端 {client_id} 异常: {error}")
    finally:
        await message_service.disconnect(client_id)


async def _handle_message(
    websocket: WebSocket, client_id: str, raw: str
) -> None:
    """解析 JSON 并调用业务服务，发送响应或错误消息。"""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        await _send_error(websocket, "无效的 JSON 格式")
        return

    try:
        result = await message_service.dispatch(data, client_id)
    except ValueError as error:
        await _send_error(websocket, str(error))
        return

    if result is not None:
        await websocket.send_json(result)


async def _send_error(websocket: WebSocket, msg: str) -> None:
    """发送结构化错误消息。"""
    await websocket.send_json(ErrorMessage(message=msg).model_dump())
