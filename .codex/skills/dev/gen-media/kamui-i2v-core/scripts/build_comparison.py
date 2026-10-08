#!/usr/bin/env python3
"""固定テンプレートからi2v動画比較HTMLを作成する。"""

from __future__ import annotations

import html
import json
from pathlib import Path

from kamui_i2v import JapaneseArgumentParser, SKILL_ROOT, catalog_models, probe_media, require_commands


def human_size(size: int) -> str:
    if size < 1024 * 1024:
        return f"{size / 1024:.0f}KB"
    return f"{size / 1024 / 1024:.1f}MB"


def main() -> int:
    parser = JapaneseArgumentParser(description=__doc__)
    parser.add_argument("task_dir", type=Path, help="i2v出力ディレクトリ")
    parser.add_argument("--title", help="比較HTMLのタイトル")
    args = parser.parse_args()
    task_dir = args.task_dir.resolve()
    require_commands("ffprobe")
    videos = sorted(task_dir.glob("*.mp4"))
    if not videos:
        raise SystemExit(f"MP4がありません: {task_dir}")

    models = catalog_models()
    poster = next((path for path in (task_dir / "_assets").glob("source-image.*")), None)
    poster_relative = poster.relative_to(task_dir).as_posix() if poster else None
    inspection_path = task_dir / "inspection.json"
    inspections = {}
    if inspection_path.exists():
        inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
        inspections = {item["model"]: item for item in inspection.get("videos", [])}

    items = []
    for video in videos:
        model = models.get(video.stem, {})
        media = probe_media(video)
        warnings = inspections.get(video.stem, {}).get("warnings", [])
        warning_html = (
            f'<p class="video-item__warning">{html.escape(" / ".join(warnings))}</p>'
            if warnings
            else ""
        )
        poster_attr = f' poster="{html.escape(poster_relative)}"' if poster_relative else ""
        items.append(
            f"""<article class="video-item">
  <header class="video-item__header">
    <h2>{html.escape(model.get('display_name', video.stem))}</h2>
    <span class="video-item__meta">{media.get('width')} × {media.get('height')} / {human_size(video.stat().st_size)}</span>
  </header>
  {warning_html}
  <div class="video-frame">
    <video controls autoplay muted loop playsinline preload="metadata"{poster_attr}>
      <source src="{html.escape(video.name)}" type="video/mp4">
    </video>
  </div>
</article>"""
        )

    template = (SKILL_ROOT / "assets" / "comparison-template.html").read_text(encoding="utf-8")
    title = args.title or f"i2v 動画比較: {task_dir.name}"
    rendered = (
        template.replace("{{TITLE}}", html.escape(title))
        .replace("{{SUMMARY}}", f"{len(videos)}モデルを生成時の実解像度で表示")
        .replace("{{VIDEO_ITEMS}}", "\n".join(items))
    )
    (task_dir / "index.html").write_text(rendered, encoding="utf-8")
    print(task_dir / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
