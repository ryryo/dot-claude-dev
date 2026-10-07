#!/usr/bin/env python3
"""Exercise reviewed ZIP inputs and the existing bundle format with temporary files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

import build_bundle


class BuildBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.root = self.directory / "reviewed"
        self.root.mkdir()
        (self.root / "nested").mkdir()
        (self.root / "nested" / "source.txt").write_text("資料\n", encoding="utf-8")
        self.script = Path(build_bundle.__file__).resolve()

    def run_bundle(self, entries: list[str], output: Path) -> subprocess.CompletedProcess[str]:
        file_list = self.directory / "files.txt"
        file_list.write_text("\n".join(entries) + "\n", encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.script), "--root", str(self.root),
             "--files", str(file_list), "--output", str(output)],
            capture_output=True, text=True, check=False,
        )

    def test_regular_file(self) -> None:
        path, name = build_bundle.relative_file(self.root, "nested/source.txt")
        self.assertEqual(path, self.root / "nested" / "source.txt")
        self.assertEqual(name, "nested/source.txt")

    def test_internal_file_symlink_is_rejected(self) -> None:
        (self.root / "alias.txt").symlink_to("nested/source.txt")
        with self.assertRaises(ValueError):
            build_bundle.relative_file(self.root, "alias.txt")

    def test_internal_directory_symlink_is_rejected(self) -> None:
        (self.root / "alias").symlink_to("nested", target_is_directory=True)
        with self.assertRaises(ValueError):
            build_bundle.relative_file(self.root, "alias/source.txt")

    def test_external_and_dangling_symlinks_are_rejected(self) -> None:
        (self.directory / "outside.txt").write_text("outside", encoding="utf-8")
        for name, target in (("external.txt", "../outside.txt"), ("dangling.txt", "absent.txt")):
            with self.subTest(name=name):
                (self.root / name).symlink_to(target)
                with self.assertRaises(ValueError):
                    build_bundle.relative_file(self.root, name)

    def test_missing_files_and_directories_are_rejected(self) -> None:
        for name in ("missing.txt", "nested"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build_bundle.relative_file(self.root, name)

    def test_secret_names_and_outside_paths_are_rejected(self) -> None:
        names = ("", ".env", ".env.test", "credentials.json", "../outside.txt",
                 str(self.directory / "outside.txt"))
        for name in names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                build_bundle.relative_file(self.root, name)

    def test_cli_preserves_manifest_and_deterministic_contents(self) -> None:
        (self.root / "README.md").write_text("# Reviewed example\n", encoding="utf-8")
        entries = ["nested/source.txt", "README.md"]
        outputs = [self.directory / "first.zip", self.directory / "second.zip"]
        for output in outputs:
            result = self.run_bundle(entries, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["files"], 2)
        self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
        with ZipFile(outputs[0]) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.namelist(), ["README.md", "nested/source.txt", "BUNDLE-MANIFEST.json"])
            manifest = json.loads(archive.read("BUNDLE-MANIFEST.json"))
            self.assertEqual(manifest["format"], 1)
            self.assertEqual(manifest["root"], "reviewed file list; local root intentionally omitted")
            expected = []
            for name in sorted(entries):
                data = (self.root / name).read_bytes()
                self.assertEqual(archive.read(name), data)
                expected.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            self.assertEqual(manifest["files"], expected)
            self.assertNotIn(str(self.root), archive.read("BUNDLE-MANIFEST.json").decode("utf-8"))
            self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_cli_rejected_link_does_not_create_archive(self) -> None:
        (self.root / "alias.txt").symlink_to("nested/source.txt")
        output = self.directory / "rejected.zip"
        result = self.run_bundle(["alias.txt"], output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_cli_rejects_duplicate_entries_and_output_inside_root(self) -> None:
        for entries, output in (
            (["nested/source.txt", "nested/source.txt"], self.directory / "duplicate.zip"),
            (["nested/source.txt"], self.root / "inside.zip"),
        ):
            with self.subTest(output=output.name):
                result = self.run_bundle(entries, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
