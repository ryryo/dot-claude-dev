#!/usr/bin/env python3
"""互換用: kamui-i2v-coreの共通モジュールを再エクスポートする。"""

from __future__ import annotations

import importlib.util
from pathlib import Path


_SKILL_ROOT = Path(__file__).resolve().parent.parent
_CORE_MODULE = _SKILL_ROOT.parent / "kamui-i2v-core" / "scripts" / "kamui_i2v.py"
_SPEC = importlib.util.spec_from_file_location("_kamui_i2v_core", _CORE_MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"kamui-i2v-coreを読み込めません: {_CORE_MODULE}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

for _name in dir(_MODULE):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_MODULE, _name)

__all__ = [_name for _name in globals() if not _name.startswith("_")]
