#!/usr/bin/env python3
"""人物メッセージi2v用の互換ラッパー。実装はkamui-i2v-coreに置く。"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    skill_root = Path(__file__).resolve().parent.parent
    core_scripts = skill_root.parent / "kamui-i2v-core" / "scripts"
    core_generate = core_scripts / "generate.py"
    args = sys.argv[1:]
    has_mode = any(arg == "--mode" or arg.startswith("--mode=") for arg in args)
    if not has_mode:
        args = ["--mode", "message", *args]
    sys.path.insert(0, str(core_scripts))
    sys.argv = [str(core_generate), *args]
    runpy.run_path(str(core_generate), run_name="__main__")


if __name__ == "__main__":
    main()
