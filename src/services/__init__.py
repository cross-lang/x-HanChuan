"""业务服务层。

不再导出模块级单例；实例由 main.py lifespan 创建并注入到 app.state。
外部应通过 app.state.message_service 或 FastAPI Depends 获取实例。
"""

from .message_service import MessageService

__all__ = ["MessageService"]
