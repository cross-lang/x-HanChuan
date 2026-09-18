#!/usr/bin/env python
"""
Broadcast 广播客户端

一对多通信模式：
  客户端 A 发送消息 → 服务器转发给所有已连接客户端

用法：
  uv run python examples/02_broadcast.py
"""
import asyncio
import json
import websockets


async def listen(ws) -> None:
    """后台协程：持续接收服务器广播的消息"""
    async for raw in ws:
        data = json.loads(raw)
        msg_type = data.get("type")

        if msg_type == "broadcast":
            sender = data.get("sender", "未知")
            content = data.get("content", "")
            print(f"\n  [广播] 来自 {sender[:8]}: {content}")
        elif msg_type == "connected":
            print(f"[客户端] 已连接，client_id = {data['client_id']}")


async def main() -> None:
    uri = "ws://localhost:8000/api/v1/channel"

    async with websockets.connect(uri) as ws:
        # 启动后台监听
        listen_task = asyncio.create_task(listen(ws))

        print("输入消息进行广播（输入 quit 退出）：")
        try:
            while True:
                content = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )
                if content.strip().lower() == "quit":
                    break
                await ws.send(json.dumps({
                    "type": "broadcast",
                    "content": content,
                }))
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            listen_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
