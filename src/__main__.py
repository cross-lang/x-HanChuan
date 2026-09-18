"""
x-websocket CLI 入口

提供以下命令：
- serve: 启动 WebSocket 服务器
- config: 查看当前配置
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .server import app
from .core.config import settings
from .core.logger import logger, setup_logging

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="x-websocket")
def cli() -> None:
    """x-websocket — 基于 WebSocket 协议的实时通信演示"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="服务器监听地址")
@click.option("--port", default=8765, type=int, help="服务器监听端口")
@click.option("--reload", is_flag=True, help="启用热重载（开发模式）")
def serve(host: str, port: int, reload: bool) -> None:
    """启动 WebSocket 服务器"""
    import uvicorn

    # 初始化日志系统
    setup_logging()

    console.print(
        Panel.fit(
            f"[bold green]x-websocket[/bold green] 服务器启动中...\n"
            f"地址: [cyan]ws://{host}:{port}/ws[/cyan]\n"
            f"热重载: [cyan]{'是' if reload else '否'}[/cyan]\n"
            f"API 文档: [cyan]http://{host}:{port}/docs[/cyan]",
            title="服务器配置",
        )
    )

    logger.info(f"服务器启动中：{host}:{port}")

    uvicorn.run(
        "src.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@cli.command()
def config() -> None:
    """查看当前配置"""
    table = Table(title="当前配置", show_header=True, header_style="bold magenta")
    table.add_column("配置项", style="dim", width=20)
    table.add_column("值", style="cyan")

    table.add_row("服务器地址", settings.host)
    table.add_row("服务器端口", str(settings.port))
    table.add_row("调试模式", str(settings.debug))
    table.add_row("日志级别", settings.log_level)

    console.print(table)


def main() -> None:
    """主入口函数（pyproject.toml 中的 entry point）"""
    cli()


if __name__ == "__main__":
    main()