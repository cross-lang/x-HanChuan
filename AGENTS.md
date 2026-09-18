# AGENTS.md — AI 代理编码指南

> 项目概况、安装步骤、示例说明、技术栈等详见 [README.md](README.md)。

## 构建与运行

```bash
uv sync --dev
uv run x-HanChuan                          # 0.0.0.0:8000
uv run x-HanChuan --port 9000 --reload
uv run x-HanChuan --help                   # 查看帮助
```

## 关键文件

| 文件 | 职责 |
|---|---|
| `src/main.py` | FastAPI 应用入口、CLI 入口（argparse）与路由注册 |
| `src/api/router.py` | 路由聚合器（统一注册 v1 路由） |
| `src/api/v1/health.py` | 系统路由（/health、/version） |
| `src/api/v1/message.py` | WebSocket 路由（/channel）及管理接口 |
| `src/core/config.py` | dataclass + YAML 配置（`settings` 单例） |
| `src/core/logger.py` | loguru 日志（`logger` / `setup_logging`） |
| `src/constants/` | 全局常量与枚举（`APP_NAME` / `MessageType` 等） |
| `src/schemas/message.py` | Pydantic 数据模型与 `MessageType` 枚举 |
| `src/connection/manager.py` | 连接管理器（注册/注销/广播/房间） |
| `src/services/message_service.py` | 消息业务处理（echo/broadcast/chat/ping） |
| `examples/01_*.py` – `04_*.py` | 四个参考客户端实现 |
| `Dockerfile` / `docker-compose.yml` | Docker 构建与编排 |
| `uv.toml` | uv 包管理器配置 |
| `uv.lock` | 依赖锁定文件（提交到 Git） |

## 编码规范

- **语言**: 文档字符串、注释、日志消息、CLI 帮助使用**简体中文**；变量名/代码标识符使用英文
- **导入**: `src/` 内使用相对导入（`from ..schemas.message import ...`）
- **文档字符串**: Google 风格，包含 `Args:`、`Returns:`、`Raises:` 段落，使用中文
- **类型标注**: 所有函数签名均需类型注解
- **异步**: WebSocket 处理函数均为 `async`
- **日志**: 使用 loguru，从 `src.core.logger` 导入 `logger`；消息使用中文
- **命名**: 类名 PascalCase，函数名 snake_case，私有方法 `_前缀`，枚举成员 UPPER_SNAKE_CASE
- **行宽**: 88（ruff + black）
- **错误处理**: 关闭连接前通过 WebSocket 发送结构化 `ErrorMessage`

## 消息类型

`MessageType` 枚举定义在 `src/schemas/message.py`：

| 类型 | 处理函数 | 说明 |
|---|---|---|
| `echo` | `_handle_echo` | 原样返回 |
| `broadcast` | `_handle_broadcast` | 广播给所有人 |
| `chat` | `_handle_chat` | 房间内转发（不含发送者） |
| `ping` | `_handle_ping` | 返回 pong |

新增消息类型：在 `MessageType` 枚举中添加 → 在 `_dispatch()` 中添加路由 → 实现 `_handle_xxx()` 函数。

## 注意事项

1. **测试目录缺失** — `tests/` 尚未创建
2. **CORS 允许所有来源** — 开发环境 `origins=["*"]`，生产环境需收紧
3. **配置优先级** — 环境变量 > config.{env}.yaml > config.yaml > 代码默认值
4. **loguru 初始化** — `setup_logging()` 在 CLI 启动和 `lifespan` 事件中各调用一次，内部有 `_configured` 防重入
5. **uv.lock 提交到 Git** — 保证所有环境依赖一致

## 文档链接

- [README.md](README.md) — 完整中文文档
- [README.en.md](README.en.md) — 英文版文档
- [.env.example](.env.example) — 环境变量说明
