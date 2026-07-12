from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"


def run_script(name: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def make_cell(path: Path, width: int, height: int, bottom: int = 203) -> None:
    image = Image.new("RGBA", (192, 208), (0, 0, 0, 0))
    left = (192 - width) // 2
    top = bottom - height
    ImageDraw.Draw(image).rectangle((left, top, left + width - 1, bottom - 1), fill=(240, 180, 20, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_state(root: Path, state: str, count: int, heights: list[int], bottoms: list[int] | None = None) -> None:
    if bottoms is None:
        bottoms = [203] * count
    for index in range(count):
        make_cell(root / state / f"frame-{index:02d}.png", 110, heights[index], bottoms[index])


class WorkflowScriptsTest(unittest.TestCase):
    def test_prepare_canonical_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = Image.new("RGBA", (400, 500), (0, 0, 0, 0))
            ImageDraw.Draw(source).rectangle((100, 50, 299, 449), fill=(255, 210, 20, 255))
            source_path = root / "source.png"
            source.save(source_path)
            output = root / "canonical-cell.png"
            report = root / "report.json"
            run_script(
                "prepare_canonical_cell.py",
                "--input",
                str(source_path),
                "--output",
                str(output),
                "--report-json",
                str(report),
            )
            with Image.open(output) as image:
                self.assertEqual(image.size, (192, 208))
                self.assertEqual(image.getchannel("A").getbbox()[3], 203)
            data = json.loads(report.read_text())
            self.assertEqual(data["sprite_size"][1], 190)

    def test_large_geometry_correction_fails_then_repair_mode_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frames = root / "frames"
            make_state(frames, "idle", 6, [190] * 6)
            make_state(frames, "running-right", 8, [184, 186, 185, 184, 186, 185, 184, 186])
            make_state(frames, "jumping", 5, [120, 140, 135, 140, 120], [203, 178, 145, 178, 203])

            report = root / "failed-report.json"
            result = run_script(
                "normalize_pet_geometry.py",
                "--input-frames-root",
                str(frames),
                "--output-frames-root",
                str(root / "normal-default"),
                "--report-json",
                str(report),
                "--states",
                "idle,running-right,jumping",
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            failed = json.loads(report.read_text())
            self.assertFalse(failed["ok"])
            self.assertTrue(any("再生成" in error for error in failed["errors"]))

            repaired_report = root / "repaired-report.json"
            run_script(
                "normalize_pet_geometry.py",
                "--input-frames-root",
                str(frames),
                "--output-frames-root",
                str(root / "normal-repair"),
                "--report-json",
                str(repaired_report),
                "--states",
                "idle,running-right,jumping",
                "--allow-large-correction",
                "--repair-max-scale",
                "1.38",
            )
            repaired = json.loads(repaired_report.read_text())
            self.assertTrue(repaired["ok"])
            self.assertEqual(repaired["rows"]["jumping"]["output_vertical_range"], 10)
            self.assertGreaterEqual(repaired["rows"]["jumping"]["output_max_height_ratio"], 0.92)
            self.assertGreaterEqual(
                min(repaired["rows"]["jumping"]["output_widths"]) / repaired["target_width"],
                0.88,
            )

    def test_row_scale_preserves_crouch_difference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frames = root / "frames"
            make_state(frames, "idle", 6, [190] * 6)
            make_state(frames, "failed", 8, [190, 175, 150, 125, 100, 125, 160, 190])
            report = root / "report.json"
            run_script(
                "normalize_pet_geometry.py",
                "--input-frames-root",
                str(frames),
                "--output-frames-root",
                str(root / "normalized"),
                "--report-json",
                str(report),
                "--states",
                "idle,failed",
            )
            data = json.loads(report.read_text())
            heights = data["rows"]["failed"]["output_heights"]
            self.assertLess(heights[4], heights[0] * 0.6)

    def test_chroma_preprocess_and_transition_previews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decoded = root / "decoded"
            decoded.mkdir()
            strip = Image.new("RGB", (384, 208), (0, 0, 250))
            ImageDraw.Draw(strip).rectangle((60, 30, 140, 202), fill=(250, 200, 20))
            ImageDraw.Draw(strip).rectangle((240, 30, 320, 202), fill=(250, 200, 20))
            strip.save(decoded / "idle.png")
            output = root / "decoded-clean"
            report = root / "chroma.json"
            run_script(
                "preprocess_chroma_rows.py",
                "--input-dir",
                str(decoded),
                "--output-dir",
                str(output),
                "--report-json",
                str(report),
                "--states",
                "idle",
            )
            with Image.open(output / "idle.png") as processed:
                self.assertEqual(processed.size, strip.size)
                self.assertEqual(processed.convert("RGBA").getchannel("A").getpixel((0, 0)), 0)

            frames = root / "frames"
            make_state(frames, "idle", 6, [190] * 6)
            make_state(frames, "jumping", 5, [160, 185, 190, 185, 160], [203, 198, 193, 198, 203])
            make_state(frames, "failed", 8, [190, 175, 150, 125, 100, 125, 160, 190])
            transitions = root / "transitions"
            transition_report = root / "transitions.json"
            run_script(
                "render_transition_previews.py",
                "--frames-root",
                str(frames),
                "--output-dir",
                str(transitions),
                "--report-json",
                str(transition_report),
            )
            self.assertTrue((transitions / "idle-to-jumping-to-idle.gif").is_file())
            self.assertTrue((transitions / "idle-to-jumping-to-idle@3x.gif").is_file())
            with Image.open(transitions / "idle-to-jumping-to-idle.gif") as gif:
                self.assertEqual(gif.size, (192, 208))

    def test_safe_package_promote_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / "codex-home"
            candidate = root / "candidate"
            run_summary = root / "run-summary.json"
            sprite1 = root / "v1.webp"
            sprite1.write_bytes(b"version-1")
            run_script(
                "package_pet_safely.py",
                "stage",
                "--spritesheet",
                str(sprite1),
                "--candidate-dir",
                str(candidate),
                "--pet-id",
                "test-pet",
                "--display-name",
                "Test Pet",
                "--description",
                "test",
                "--run-summary",
                str(run_summary),
            )
            self.assertEqual(json.loads(run_summary.read_text())["acceptance_status"], "provisional")
            blocked = run_script(
                "package_pet_safely.py",
                "promote",
                "--candidate-dir",
                str(candidate),
                "--codex-home",
                str(codex_home),
                "--confirm-in-app-accepted",
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertFalse((codex_home / "pets/test-pet").exists())
            run_script(
                "package_pet_safely.py",
                "preview",
                "--candidate-dir",
                str(candidate),
                "--codex-home",
                str(codex_home),
                "--run-summary",
                str(run_summary),
            )
            preview_destination = codex_home / "pets/test-pet-candidate/spritesheet.webp"
            self.assertEqual(preview_destination.read_bytes(), b"version-1")
            self.assertEqual(json.loads(run_summary.read_text())["acceptance_status"], "preview_installed")
            run_script(
                "package_pet_safely.py",
                "promote",
                "--candidate-dir",
                str(candidate),
                "--codex-home",
                str(codex_home),
                "--confirm-in-app-accepted",
                "--run-summary",
                str(run_summary),
            )
            destination = codex_home / "pets/test-pet/spritesheet.webp"
            self.assertEqual(destination.read_bytes(), b"version-1")
            self.assertFalse(preview_destination.exists())
            self.assertEqual(json.loads(run_summary.read_text())["acceptance_status"], "in_app_accepted")

            sprite2 = root / "v2.webp"
            sprite2.write_bytes(b"version-2")
            run_script(
                "package_pet_safely.py",
                "stage",
                "--spritesheet",
                str(sprite2),
                "--candidate-dir",
                str(candidate),
                "--pet-id",
                "test-pet",
                "--display-name",
                "Test Pet",
                "--description",
                "test",
                "--force",
                "--run-summary",
                str(run_summary),
            )
            run_script(
                "package_pet_safely.py",
                "preview",
                "--candidate-dir",
                str(candidate),
                "--codex-home",
                str(codex_home),
                "--run-summary",
                str(run_summary),
            )
            self.assertEqual(preview_destination.read_bytes(), b"version-2")
            run_script(
                "package_pet_safely.py",
                "promote",
                "--candidate-dir",
                str(candidate),
                "--codex-home",
                str(codex_home),
                "--confirm-in-app-accepted",
                "--run-summary",
                str(run_summary),
            )
            self.assertEqual(destination.read_bytes(), b"version-2")
            run_script(
                "package_pet_safely.py",
                "rollback",
                "--pet-id",
                "test-pet",
                "--codex-home",
                str(codex_home),
                "--run-summary",
                str(run_summary),
            )
            self.assertEqual(destination.read_bytes(), b"version-1")
            self.assertEqual(json.loads(run_summary.read_text())["acceptance_status"], "rolled_back")


if __name__ == "__main__":
    unittest.main()
