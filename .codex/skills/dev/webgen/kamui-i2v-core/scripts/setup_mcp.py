#!/usr/bin/env python3
"""対象プロジェクトへKamui i2v MCP設定を安全にマージする。"""

from __future__ import annotations

import json
from pathlib import Path

from kamui_i2v import JapaneseArgumentParser, catalog_models, ensure_project_mcp, select_models


def main() -> int:
    parser = JapaneseArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="対象プロジェクトのルート")
    parser.add_argument("--model", action="append", dest="models", help="設定するモデルslug。複数指定可")
    parser.add_argument("--all-models", action="store_true", help="有効な全モデルを設定する")
    parser.add_argument("--list-models", action="store_true", help="モデル一覧を表示する")
    args = parser.parse_args()

    if args.list_models:
        for model in catalog_models().values():
            print(f"{model['slug']}\t{model['display_name']}\t{model['mcp']['server_id']}")
        return 0

    if args.all_models:
        models = [model for model in catalog_models().values() if model.get("enabled")]
    else:
        models = select_models(args.models)
    result = ensure_project_mcp(args.project.resolve(), models)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
