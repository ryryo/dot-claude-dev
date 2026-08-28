#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


VALIDATOR = Path(__file__).with_name("validate_plan_topology.py")
START = "<!-- parallelization-topology:start -->"
END = "<!-- parallelization-topology:end -->"


def valid_manifest() -> dict:
    return {
        "schemaVersion": 1,
        "gate": "parallelization-topology",
        "integrationPlan": "docs/PLAN/260826_integration.md",
        "lanes": [
            {
                "id": "shared-seam",
                "plan": "docs/PLAN/260828_shared-seam.md",
                "section": "Phase A",
                "execution": "local",
                "writeScopes": ["apps/web/src/playback/**"],
                "externalStates": [],
            },
            {
                "id": "editing",
                "plan": "docs/PLAN/260826_integration.md",
                "section": "Phase E",
                "execution": "local",
                "writeScopes": ["apps/web/src/editing/**"],
                "externalStates": [],
            },
            {
                "id": "diagnostics",
                "plan": "docs/PLAN/260827_diagnostics.md",
                "section": "Phase B",
                "execution": "local",
                "writeScopes": ["apps/web/src/diagnostics/**"],
                "externalStates": [],
            },
            {
                "id": "release",
                "plan": "docs/PLAN/260826_release.md",
                "section": "Phase A",
                "execution": "external",
                "writeScopes": ["docs/EVIDENCE/release.md"],
                "externalStates": ["cloudflare:production"],
            },
            {
                "id": "join",
                "plan": "docs/PLAN/260826_integration.md",
                "section": "Phase G",
                "execution": "local",
                "writeScopes": ["docs/USER_STORIES.md"],
                "externalStates": [],
            },
        ],
        "edges": [
            {
                "from": "shared-seam",
                "to": "editing",
                "classification": "shared-seam",
                "reason": "consumer starts after the producer contract is frozen",
                "evidence": "handoff Gate P",
                "handoff": "schedule projection contract",
            },
            {
                "from": "shared-seam",
                "to": "diagnostics",
                "classification": "shared-seam",
                "reason": "consumer starts after the observer contract is frozen",
                "evidence": "handoff Gate P",
                "handoff": "readonly observer contract",
            },
            {
                "from": "editing",
                "to": "join",
                "classification": "join",
                "reason": "final verification consumes the editing result",
                "evidence": "Gate E",
                "handoff": "reviewed editing result",
            },
            {
                "from": "diagnostics",
                "to": "join",
                "classification": "join",
                "reason": "final verification consumes the diagnostics result",
                "evidence": "Candidate Gate C",
                "handoff": "reviewed diagnostics result",
            },
        ],
        "waves": [
            {"id": "wave-1", "lanes": ["release", "shared-seam"]},
            {"id": "wave-2", "lanes": ["diagnostics", "editing"]},
            {"id": "wave-3", "lanes": ["join"]},
        ],
    }


def render_plan(manifest: dict, *, extra_block: bool = False) -> str:
    block = f"{START}\n```json\n{json.dumps(manifest, ensure_ascii=False, indent=2)}\n```\n{END}"
    if extra_block:
        block = f"{block}\n\n{block}"
    return f"# Integration PLAN\n\n{block}\n"


def run_validator(
    manifest: dict,
    *,
    extra_block: bool = False,
    missing_plan: str | None = None,
    validated_plan: str | None = None,
    missing_section_plan: str | None = None,
    fenced_section_plan: str | None = None,
    escaping_plan: str | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        root = workspace / "repo"
        root.mkdir()
        plan_path = root / (validated_plan or manifest["integrationPlan"])
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        integration_sections = [
            lane.get("section")
            for lane in manifest.get("lanes", [])
            if lane.get("plan") == (validated_plan or manifest["integrationPlan"])
            and isinstance(lane.get("section"), str)
        ]
        plan_path.write_text(
            render_plan(manifest, extra_block=extra_block)
            + "".join(f"\n## {section} — Work\n" for section in integration_sections),
            encoding="utf-8",
        )
        for lane in manifest.get("lanes", []):
            lane_plan = lane.get("plan")
            if not isinstance(lane_plan, str) or lane_plan == manifest["integrationPlan"]:
                continue
            if lane_plan == missing_plan:
                continue
            lane_path = root / lane_plan
            lane_path.parent.mkdir(parents=True, exist_ok=True)
            if lane_plan == escaping_plan:
                outside = workspace / "outside.md"
                outside.write_text(f"# {lane['section']}\n", encoding="utf-8")
                lane_path.symlink_to(outside)
                continue
            section = "Missing section" if lane_plan == missing_section_plan else lane["section"]
            if lane_plan == fenced_section_plan:
                lane_path.write_text(f"```markdown\n# {section}\n```\n", encoding="utf-8")
            else:
                lane_path.write_text(f"# {section}\n", encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(root), str(plan_path)],
            text=True,
            capture_output=True,
            check=False,
        )


class PlanTopologyValidatorTest(unittest.TestCase):
    def test_valid_maximally_parallel_topology_passes(self) -> None:
        result = run_validator(valid_manifest())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("local concurrency 2", result.stdout)
        self.assertIn("serialized exceptions 0", result.stdout)

    def test_requires_exactly_one_manifest_block(self) -> None:
        result = run_validator(valid_manifest(), extra_block=True)
        self.assertEqual(1, result.returncode)
        self.assertIn("1個", result.stderr)

    def test_rejects_same_wave_write_scope_overlap(self) -> None:
        manifest = valid_manifest()
        manifest["lanes"][2]["writeScopes"] = ["apps/web/src/editing/history.ts"]
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("write scope", result.stderr)
        self.assertIn("editing", result.stderr)
        self.assertIn("diagnostics", result.stderr)

    def test_rejects_same_wave_external_state_overlap(self) -> None:
        manifest = valid_manifest()
        manifest["lanes"][0]["externalStates"] = ["cloudflare:production"]
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("external state", result.stderr)

    def test_rejects_cycle(self) -> None:
        manifest = valid_manifest()
        manifest["edges"].append(
            {
                "from": "join",
                "to": "shared-seam",
                "classification": "hard-dependency",
                "reason": "invalid cycle",
                "evidence": "none",
                "handoff": "none",
            }
        )
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("閉路", result.stderr)

    def test_declared_waves_must_match_earliest_topological_waves(self) -> None:
        manifest = valid_manifest()
        manifest["waves"] = [
            {"id": "wave-1", "lanes": ["release", "shared-seam"]},
            {"id": "wave-2", "lanes": ["editing"]},
            {"id": "wave-3", "lanes": ["diagnostics"]},
            {"id": "wave-4", "lanes": ["join"]},
        ]
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("最早wave", result.stderr)

    def test_dependency_edge_requires_classification_and_evidence(self) -> None:
        manifest = valid_manifest()
        del manifest["edges"][0]["evidence"]
        manifest["edges"][0]["classification"] = "because-we-said-so"
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("classification", result.stderr)
        self.assertIn("evidence", result.stderr)

    def test_overlapping_dependency_requires_serialized_exception_review(self) -> None:
        manifest = valid_manifest()
        manifest["lanes"][1]["writeScopes"] = ["apps/web/src/playback/native.ts"]
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("serialized-exception", result.stderr)

    def test_serialized_exception_requires_all_alternative_rejection_reasons(self) -> None:
        manifest = valid_manifest()
        manifest["lanes"][1]["writeScopes"] = ["apps/web/src/playback/native.ts"]
        manifest["edges"][0].update(
            {
                "classification": "serialized-exception",
                "resources": ["apps/web/src/playback/native.ts"],
                "criticalPathImpact": "editing waits for the shared-seam lane",
                "alternatives": {
                    "narrow-scope": "the file contains the indivisible public contract",
                    "shared-seam": "already represented by the predecessor lane",
                },
            }
        )
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("join-only", result.stderr)

    def test_complete_serialized_exception_can_order_an_overlap(self) -> None:
        manifest = valid_manifest()
        manifest["lanes"][1]["writeScopes"] = ["apps/web/src/playback/native.ts"]
        manifest["edges"][0].update(
            {
                "classification": "serialized-exception",
                "resources": ["apps/web/src/playback/native.ts"],
                "criticalPathImpact": "editing waits for the shared-seam lane",
                "alternatives": {
                    "narrow-scope": "the public change and consumer update are inseparable",
                    "shared-seam": "the predecessor already is the smallest shared seam",
                    "join-only": "the consumer cannot compile before the contract exists",
                },
            }
        )
        result = run_validator(manifest)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("serialized exceptions 1", result.stdout)

    def test_rejects_ambiguous_globs_and_absolute_paths(self) -> None:
        for invalid_scope in ("apps/*/src", "/tmp/plan-output"):
            with self.subTest(invalid_scope=invalid_scope):
                manifest = copy.deepcopy(valid_manifest())
                manifest["lanes"][0]["writeScopes"] = [invalid_scope]
                result = run_validator(manifest)
                self.assertEqual(1, result.returncode)
                self.assertIn("writeScopes", result.stderr)

    def test_malformed_lane_reports_gate_errors_without_traceback(self) -> None:
        manifest = valid_manifest()
        del manifest["lanes"][0]["execution"]
        del manifest["lanes"][0]["writeScopes"]
        del manifest["lanes"][0]["externalStates"]
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("execution", result.stderr)
        self.assertIn("writeScopes", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_referenced_lane_plan_must_exist(self) -> None:
        manifest = valid_manifest()
        missing = manifest["lanes"][2]["plan"]
        result = run_validator(manifest, missing_plan=missing)
        self.assertEqual(1, result.returncode)
        self.assertIn("存在しません", result.stderr)

    def test_integration_plan_field_must_name_the_validated_plan(self) -> None:
        manifest = valid_manifest()
        result = run_validator(
            manifest, validated_plan="docs/PLAN/not-the-integration-plan.md"
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("検証対象PLAN", result.stderr)

    def test_lane_section_must_exist_as_a_heading_in_its_plan(self) -> None:
        manifest = valid_manifest()
        plan = manifest["lanes"][2]["plan"]
        result = run_validator(manifest, missing_section_plan=plan)
        self.assertEqual(1, result.returncode)
        self.assertIn("section", result.stderr)
        self.assertIn("見出し", result.stderr)

    def test_lane_plan_symlink_cannot_escape_repository_root(self) -> None:
        manifest = valid_manifest()
        plan = manifest["lanes"][2]["plan"]
        result = run_validator(manifest, escaping_plan=plan)
        self.assertEqual(1, result.returncode)
        self.assertIn("root外", result.stderr)

    def test_heading_inside_a_fenced_example_does_not_satisfy_section(self) -> None:
        manifest = valid_manifest()
        plan = manifest["lanes"][2]["plan"]
        result = run_validator(manifest, fenced_section_plan=plan)
        self.assertEqual(1, result.returncode)
        self.assertIn("見出し", result.stderr)

    def test_two_lanes_cannot_claim_the_same_plan_section(self) -> None:
        manifest = valid_manifest()
        manifest["lanes"][2]["plan"] = manifest["lanes"][1]["plan"]
        manifest["lanes"][2]["section"] = manifest["lanes"][1]["section"]
        result = run_validator(manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("同じPLAN section", result.stderr)


if __name__ == "__main__":
    unittest.main()
