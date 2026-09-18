#!/usr/bin/env python
"""
示例 01 — Echo（回显）

演示 WebSocket 最基础的通信模式：
  客户端发送消息 → 服务器原样返回

运行方式：
  1. 启动服务器: x-websocket serve
  2. 运行本示例: python examples/01_echo.py
"""
import asyncio
import json
import websockets


async def main() -> None:
    uri = "ws://localhost:8765/ws"

    async with websockets.connect(uri) as ws:
        # 接收连接确认消息
        connected = json.loads(await ws.recv())
        print(f"[客户端] 已连接，client_id = {connected['client_id']}")

        # 发送 Echo 消息
        messages = ["你好，WebSocket！", "这是第二条消息", "Echo 测试完毕"]
        for msg in messages:
            await ws.send(json.dumps({"type": "echo", "content": msg}))
            print(f"[客户端] 发送 → {msg}")

            # 接收服务器回显
            response = json.loads(await ws.recv())
            print(f"[客户端] 收到 ← {response['content']}")

        print("\n[Echo 示例完成]")


if __name__ == "__main__":
    asyncio.run(main())
