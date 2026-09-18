#!/usr/bin/env python
"""
示例 03 — Room Chat（房间聊天）

演示房间（Room）机制：
  客户端加入同一房间后，消息仅转发给房间内的其他成员。

运行方式：
  1. 启动服务器: x-websocket serve
  2. 打开两个终端，分别运行:
     python examples/03_room_chat.py
     python examples/03_room_chat.py
  3. 两个客户端自动加入同一房间，输入消息即可互相聊天
"""
import asyncio
import json
import websockets


ROOM_ID = "demo_room"  # 所有客户端加入同一个房间


async def listen(ws) -> None:
    """后台协程：持续接收房间内的消息"""
    async for raw in ws:
        data = json.loads(raw)
        msg_type = data.get("type")

        if msg_type == "chat":
            sender = data.get("sender", "未知")
            content = data.get("content", "")
            room = data.get("room_id", "")
            print(f"\n  [房间 {room}] {sender[:8]}: {content}")
        elif msg_type == "connected":
            print(f"[客户端] 已连接，client_id = {data['client_id']}")


async def main() -> None:
    uri = "ws://localhost:8765/ws"

    async with websockets.connect(uri) as ws:
        listen_task = asyncio.create_task(listen(ws))

        print(f"已加入房间 [{ROOM_ID}]，输入消息聊天（输入 quit 退出）：")
        try:
            while True:
                content = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )
                if content.strip().lower() == "quit":
                    break
                await ws.send(json.dumps({
                    "type": "chat",
                    "content": content,
                    "room_id": ROOM_ID,
                }))
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            listen_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
