#!/usr/bin/env python3
"""导出 OpenAPI 文档为可被 Postman 导入的 JSON 文件。

使用方式:
    uv run python scripts/export_openapi.py
    uv run python scripts/export_openapi.py --url http://127.0.0.1:9000/openapi.json

导出的文件可直接通过 Postman → Import → File 导入。
"""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DEFAULT_URL = "http://127.0.0.1:8000/openapi.json"


def export_openapi(url: str, output_dir: Path) -> Path:
    """从运行中的 FastAPI 服务获取 OpenAPI JSON 并保存。

    Args:
        url: OpenAPI JSON 端点地址
        output_dir: 输出目录

    Returns:
        保存的文件路径
    """
    print(f"正在获取 OpenAPI 文档: {url}")
    with urlopen(url) as resp:
        spec = json.loads(resp.read().decode("utf-8"))

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "x-HanChuan.postman-openapi.json"
    output_file.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    paths_count = len(spec.get("paths", {}))
    tags = set()
    for path_info in spec.get("paths", {}).values():
        for op in path_info.values():
            if isinstance(op, dict):
                tags.update(op.get("tags", []))

    print(f"导出成功: {output_file}")
    print(f"  路径数量: {paths_count}")
    print(f"  文件夹结构: {sorted(tags)}")
    print(f"  导入方式: Postman → Import → File → 选择 {output_file.name}")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="导出 FastAPI OpenAPI 文档供 Postman 导入"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"OpenAPI JSON 端点地址（默认 {DEFAULT_URL}）",
    )
    parser.add_argument(
        "--output",
        default=str(DOCS_DIR),
        help=f"输出目录（默认 {DOCS_DIR}）",
    )
    args = parser.parse_args()

    export_openapi(args.url, Path(args.output))


if __name__ == "__main__":
    main()
