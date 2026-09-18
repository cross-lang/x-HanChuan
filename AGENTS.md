# AGENTS.md — AI 代理编码指南

> 项目概况、安装步骤、示例说明、技术栈等详见 [README.md](README.md)。

## 构建与运行

```bash
uv venv && uv pip install -e ".[dev]"
x-websocket serve                    # 0.0.0.0:8765
x-websocket serve --port 9000 --reload
x-websocket config                   # 查看当前配置
```

## 关键文件

| 文件 | 职责 |
|---|---|
| `src/server.py` | FastAPI 应用，WebSocket 端点，消息分发 |
| `src/__main__.py` | CLI 入口（Click 命令组） |
| `src/core/config.py` | Pydantic Settings 配置（`settings` 单例） |
| `src/core/logger.py` | loguru 日志（`logger` / `setup_logging`） |
| `src/constants.py` | 全局常量（`APP_NAME` / `APP_VERSION`） |
| `src/models/message.py` | Pydantic 消息模型与 `MessageType` 枚举 |
| `src/connection/manager.py` | 连接管理器（注册/注销/广播/房间） |
| `examples/01_*.py` – `04_*.py` | 四个渐进式示例 |
| `Dockerfile` / `docker-compose.yml` | Docker 构建与编排 |
| `uv.toml` | uv 包管理器配置 |

## 编码规范

- **语言**: 文档字符串、注释、日志消息、CLI 帮助使用**简体中文**；变量名/代码标识符使用英文
- **导入**: `src/` 内使用相对导入（`from ..models.message import ...`）
- **文档字符串**: Google 风格，包含 `Args:`、`Returns:`、`Raises:` 段落，使用中文
- **类型标注**: 所有函数签名均需类型注解
- **异步**: WebSocket 处理函数均为 `async`
- **日志**: 使用 loguru，从 `src.core.logger` 导入 `logger`；消息使用中文
- **命名**: 类名 PascalCase，函数名 snake_case，私有方法 `_前缀`，枚举成员 UPPER_SNAKE_CASE
- **行宽**: 88（ruff + black）
- **错误处理**: 关闭连接前通过 WebSocket 发送结构化 `ErrorMessage`

## 消息类型

`MessageType` 枚举定义在 `src/models/message.py`：

| 类型 | 处理函数 | 说明 |
|---|---|---|
| `echo` | `_handle_echo` | 原样返回 |
| `broadcast` | `_handle_broadcast` | 广播给所有人 |
| `chat` | `_handle_chat` | 房间内转发（不含发送者） |
| `ping` | `_handle_ping` | 返回 pong |

新增消息类型：在 `MessageType` 枚举中添加 → 在 `_dispatch()` 中添加路由 → 实现 `_handle_xxx()` 函数。

## 注意事项

1. **测试目录缺失** — `tests/` 尚未创建
2. **CORS 允许所有来源** — 开发环境 `allow_origins=["*"]`，生产环境需收紧
3. **所有配置有默认值** — 无需 `.env` 即可运行
4. **loguru 初始化** — `setup_logging()` 在 CLI `serve` 命令和 `startup` 事件中各调用一次，内部有 `_configured` 防重入

## 文档链接

- [README.md](README.md) — 完整中文文档
- [README.en.md](README.en.md) — 英文版文档
- [.env.example](.env.example) — 环境变量说明
