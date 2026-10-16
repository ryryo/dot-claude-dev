from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from smoke_agents import (
    AGENTS,
    default_repo,
    is_retryable_failure,
    probe_command,
    probe_prompt,
    probe_succeeded,
)


class SmokeAgentsTest(unittest.TestCase):
    def test_default_repo_is_repository_root(self) -> None:
        self.assertEqual(Path(__file__).resolve().parents[2], default_repo())

    def test_probe_uses_persistent_parent_thread(self) -> None:
        command = probe_command(
            "codex", Path("/repo"), "pstack_skeptic", Path("/tmp/final.md")
        )
        self.assertNotIn("--ephemeral", command)
        self.assertIn("--strict-config", command)

    def test_exact_agent_inventory(self) -> None:
        self.assertEqual(
            (
                "poteto-agent",
                "comment-sicko",
                "pstack_skeptic",
                "pstack_architect",
                "pstack_minimalist",
                "thermos_correctness",
                "thermos_quality",
            ),
            AGENTS,
        )

    def test_probe_requires_child_and_parent_sentinels(self) -> None:
        prompt = probe_prompt("pstack_skeptic")
        self.assertIn("CHILD_OK:pstack_skeptic", prompt)
        self.assertIn("SPAWN_OK:pstack_skeptic", prompt)
        self.assertTrue(
            probe_succeeded(
                "pstack_skeptic",
                "collab: Wait\nCHILD_OK:pstack_skeptic\nSPAWN_OK:pstack_skeptic",
                "SPAWN_OK:pstack_skeptic",
            )
        )
        self.assertFalse(
            probe_succeeded(
                "pstack_skeptic",
                "unknown agent_type 'pstack_skeptic'\nSPAWN_OK:pstack_skeptic",
                "SPAWN_OK:pstack_skeptic",
            )
        )

    def test_only_missing_child_thread_is_retryable(self) -> None:
        self.assertTrue(
            is_retryable_failure(
                "collab spawn failed: no thread with id: 01a05790-495f-7d11-8f5c"
            )
        )
        self.assertFalse(is_retryable_failure("unknown agent_type 'pstack_skeptic'"))
        self.assertFalse(is_retryable_failure("permission denied"))
        self.assertFalse(
            probe_succeeded(
                "pstack_skeptic",
                "SPAWN_OK:pstack_skeptic",
                "SPAWN_OK:pstack_skeptic",
            )
        )


if __name__ == "__main__":
    unittest.main()
