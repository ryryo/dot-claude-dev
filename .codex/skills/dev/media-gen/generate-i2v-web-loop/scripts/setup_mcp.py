#!/usr/bin/env python3
"""互換用: kamui-i2v-coreのsetup_mcp.pyへ転送する。"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    skill_root = Path(__file__).resolve().parent.parent
    core_scripts = skill_root.parent / "kamui-i2v-core" / "scripts"
    core_script = core_scripts / "setup_mcp.py"
    sys.path.insert(0, str(core_scripts))
    sys.argv = [str(core_script), *sys.argv[1:]]
    runpy.run_path(str(core_script), run_name="__main__")


if __name__ == "__main__":
    main()
