from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_upstream import changed_paths


class CheckUpstreamTest(unittest.TestCase):
    def test_renames_and_unusual_paths_are_separate_add_delete_records(self):
        with tempfile.TemporaryDirectory(prefix="pstack upstream ") as directory:
            repo = Path(directory)
            env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_CONFIG_NOSYSTEM": "1"}

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), "-c", "core.hooksPath=" + os.devnull, *args],
                    env=env, check=True, capture_output=True, text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Upstream Test")
            git("config", "user.email", "upstream@example.invalid")
            (repo / "pstack").mkdir()
            old = "pstack/old name\twith newline\n.md"
            new = "pstack/new name\twith newline\n.md"
            (repo / old).write_text("unchanged source content\n")
            git("add", ".")
            git("commit", "-m", "baseline")
            base = git("rev-parse", "HEAD")
            (repo / old).rename(repo / new)
            git("add", "-A")
            git("commit", "-m", "rename")
            head = git("rev-parse", "HEAD")
            self.assertIn("R100", git("diff", "--name-status", "-M", base, head))
            self.assertEqual({old: "D", new: "A"}, changed_paths(repo, base, head))
            self.assertEqual({}, changed_paths(repo, head, head))


if __name__ == "__main__":
    unittest.main()
