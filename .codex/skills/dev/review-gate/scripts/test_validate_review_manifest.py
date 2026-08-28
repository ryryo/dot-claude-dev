#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


VALIDATOR = Path(__file__).with_name("validate_review_manifest.py")


def valid_brief() -> dict:
    return {
        "target": "review target",
        "gate_question": "May this advance?",
        "current_contracts": ["C1", "rendered output"],
        "handoffs": [
            {
                "id": "H1",
                "gate": "Journey Gate",
                "owner": "integration owner",
                "contract": "rendered output",
            }
        ],
        "scope_seeds": [
            {
                "id": "SC1",
                "kind": "condition",
                "source": "C1",
                "contract": "C1",
                "coverage_obligation": "must-applicable",
                "review_case_ids": ["C1-default"],
            },
            {
                "id": "SH1",
                "kind": "handoff",
                "source": "Browser Journey handoff",
                "contract": "rendered output",
                "handoff_id": "H1",
                "coverage_obligation": "handoff-pair",
                "review_case_ids": ["H1-snapshot"],
            },
        ],
    }


def valid_manifest() -> dict:
    return {
        "target": "review target",
        "gate_question": "May this advance?",
        "current_contracts": ["C1", "rendered output"],
        "scope_gate": "passed",
        "discovery_gate": "passed",
        "candidate_gate": "passed",
        "state": "candidate-sorted",
        "scope_candidates": [
            {
                "id": "S1",
                "seed_id": "SC1",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "input -> output",
                "path_id": "P1",
                "boundary": "public output",
                "review_case_ids": ["C1-default"],
            },
            {
                "id": "S2A",
                "seed_id": "SH1",
                "classification": "applicable",
                "contract": "rendered output",
                "reachable_path": "snapshot -> handoff surface",
                "path_id": "PH1",
                "boundary": "handoff surface",
                "review_case_ids": ["H1-snapshot"],
            },
            {
                "id": "S2D",
                "seed_id": "SH1",
                "classification": "downstream",
                "handoff_id": "H1",
                "gate": "Journey Gate",
                "owner": "integration owner",
                "handoff_contract": "rendered output",
                "reachable_path": "output -> browser journey",
                "path_id": "PH1",
                "handoff_review_scope_candidate_id": "S2A",
                "boundary": "handoff surface",
            },
        ],
        "review_units": [
            {
                "id": "R1",
                "scope_candidate_ids": ["S1"],
                "contract": "C1",
                "reachable_path": "input -> output",
                "path_id": "P1",
                "review_case_id": "C1-default",
                "boundary": "public output",
                "status": "satisfied",
                "evidence_mode": "static",
                "evidence": "source and consumer",
                "guarantee": "C1 on current path",
                "reviewer_id": "reviewer-1",
            },
            {
                "id": "R2",
                "scope_candidate_ids": ["S2A"],
                "contract": "rendered output",
                "reachable_path": "snapshot -> handoff surface",
                "path_id": "PH1",
                "review_case_id": "H1-snapshot",
                "boundary": "handoff surface",
                "status": "satisfied",
                "evidence_mode": "static",
                "evidence": "public snapshot",
                "guarantee": "handoff fields are produced",
                "reviewer_id": "reviewer-1",
            }
        ],
        "reviewers": [{"id": "reviewer-1", "status": "completed"}],
        "scope_tombstones": [],
        "finding_candidates": [],
    }


def scope_baseline(manifest: dict) -> dict:
    return {
        "target": manifest["target"],
        "gate_question": manifest["gate_question"],
        "current_contracts": copy.deepcopy(manifest["current_contracts"]),
        "scope_gate": "passed",
        "state": "scope-fixed",
        "scope_candidates": copy.deepcopy(manifest["scope_candidates"]),
        "scope_tombstones": copy.deepcopy(manifest.get("scope_tombstones", [])),
    }


def discovery_baseline(manifest: dict) -> dict:
    baseline = copy.deepcopy(manifest)
    baseline["state"] = "discovery-complete"
    baseline["discovery_gate"] = "passed"
    baseline.pop("candidate_gate", None)
    baseline.pop("finding_candidates", None)
    return baseline


def run_validator(
    stage: str,
    manifest: dict,
    *,
    brief: dict | None = None,
    baseline: dict | None = None,
    discovery: dict | None = None,
    previous_scope: dict | None = None,
    observation: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        directory_path = Path(directory)
        brief_path = directory_path / "brief.json"
        brief_path.write_text(json.dumps(brief or valid_brief()), encoding="utf-8")
        command = [
            sys.executable,
            str(VALIDATOR),
            "--stage",
            stage,
            "--brief",
            str(brief_path),
        ]
        if stage in {"discovery", "candidate"}:
            baseline_path = directory_path / "scope.json"
            baseline_path.write_text(
                json.dumps(baseline or scope_baseline(manifest)), encoding="utf-8"
            )
            command.extend(["--scope-baseline", str(baseline_path)])
        if stage == "scope" and previous_scope is not None:
            previous_path = directory_path / "previous-scope.json"
            previous_path.write_text(json.dumps(previous_scope), encoding="utf-8")
            command.extend(["--previous-scope-baseline", str(previous_path)])
        if stage == "scope" and observation is not None:
            observation_path = directory_path / "observation.json"
            observation_path.write_text(json.dumps(observation), encoding="utf-8")
            command.extend(["--observation-checkpoint", str(observation_path)])
        if stage == "candidate":
            discovery_path = directory_path / "discovery.json"
            discovery_path.write_text(
                json.dumps(discovery or discovery_baseline(manifest)), encoding="utf-8"
            )
            command.extend(["--discovery-baseline", str(discovery_path)])
        command.append("-")
        return subprocess.run(
            command,
            input=json.dumps(manifest),
            text=True,
            capture_output=True,
            check=False,
        )


class ReviewManifestValidatorTest(unittest.TestCase):
    def test_valid_scope_and_candidate_stages_pass(self) -> None:
        manifest = valid_manifest()
        scope = scope_baseline(manifest)
        self.assertEqual(0, run_validator("scope", scope).returncode)
        discovery = discovery_baseline(manifest)
        self.assertEqual(
            0, run_validator("discovery", discovery, baseline=scope).returncode
        )
        self.assertEqual(
            0,
            run_validator(
                "candidate", manifest, baseline=scope, discovery=discovery
            ).returncode,
        )

    def test_scope_stage_requires_exact_state(self) -> None:
        manifest = valid_manifest()
        manifest["state"] = "judged"
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("scope-fixed", result.stderr)

    def test_every_fixed_contract_needs_a_scope_seed(self) -> None:
        brief = valid_brief()
        brief["current_contracts"].append("C2")
        manifest = valid_manifest()
        manifest["current_contracts"].append("C2")
        result = run_validator("scope", manifest, brief=brief)
        self.assertEqual(1, result.returncode)
        self.assertIn("seed", result.stderr)

    def test_applicable_scope_requires_reachable_path(self) -> None:
        manifest = valid_manifest()
        del manifest["scope_candidates"][0]["reachable_path"]
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("reachable_path", result.stderr)

    def test_downstream_scope_requires_predeclared_handoff(self) -> None:
        manifest = valid_manifest()
        del manifest["scope_candidates"][2]["handoff_contract"]
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("handoff_contract", result.stderr)

    def test_scope_cannot_introduce_a_new_contract(self) -> None:
        manifest = valid_manifest()
        manifest["scope_candidates"][0]["contract"] = "future contract"
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("current_contracts", result.stderr)

    def test_manifest_cannot_expand_the_fixed_contract_set(self) -> None:
        manifest = valid_manifest()
        manifest["current_contracts"].append("general hardening")
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("Review Brief", result.stderr)

    def test_downstream_cannot_invent_a_handoff(self) -> None:
        manifest = valid_manifest()
        manifest["scope_candidates"][2].update(
            {
                "handoff_id": "future",
                "gate": "Future Gate",
                "owner": "future owner",
            }
        )
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("Review Brief", result.stderr)

    def test_every_applicable_scope_candidate_needs_a_review_unit(self) -> None:
        manifest = valid_manifest()
        manifest["scope_candidates"].append(
            {
                "id": "S4",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "boundary": "public output",
            }
        )
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("S4", result.stderr)

    def test_interrupted_reviewer_cannot_complete_gate(self) -> None:
        manifest = valid_manifest()
        manifest["reviewers"][0]["status"] = "interrupted"
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("completed", result.stderr)

    def test_reassigned_reviewer_must_transfer_to_a_completed_reviewer(self) -> None:
        manifest = valid_manifest()
        manifest["reviewers"][0] = {
            "id": "reviewer-1",
            "status": "reassigned",
            "transferred_to": "ghost",
        }
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("completed", result.stderr)

    def test_one_review_unit_cannot_cover_different_scope_candidates(self) -> None:
        manifest = valid_manifest()
        manifest["review_units"][0]["scope_candidate_ids"] = ["S1", "S2A"]
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("一つ", result.stderr)

    def test_later_gate_must_reference_predeclared_downstream(self) -> None:
        manifest = valid_manifest()
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "valid",
                "gate_effect": "does-not-block",
                "routing": "later-gate",
                "downstream_scope_candidate_id": "unknown",
                "review_unit_ids": ["R2"],
                "reason": "future verification",
            }
        ]
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("明示済み後工程", result.stderr)

    def test_contract_decision_requires_existing_contract_conflict(self) -> None:
        manifest = valid_manifest()
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "valid",
                "gate_effect": "blocks",
                "routing": "contract-decision",
                "review_unit_ids": ["R1"],
                "conflicting_contracts": ["C1"],
                "reason": "ambiguous contract",
            }
        ]
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("2件以上", result.stderr)

    def test_contract_decision_cannot_introduce_a_future_contract(self) -> None:
        manifest = valid_manifest()
        manifest["review_units"][0]["status"] = "unverified"
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "valid",
                "gate_effect": "blocks",
                "routing": "contract-decision",
                "review_unit_ids": ["R1"],
                "conflicting_contracts": ["C1", "future contract"],
                "reason": "ambiguous contract",
            }
        ]
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("current_contracts", result.stderr)

    def test_contract_decision_requires_distinct_contracts(self) -> None:
        manifest = valid_manifest()
        manifest["review_units"][0]["status"] = "unverified"
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "valid",
                "gate_effect": "blocks",
                "routing": "contract-decision",
                "review_unit_ids": ["R1"],
                "conflicting_contracts": ["C1", "C1"],
                "reason": "ambiguous contract",
            }
        ]
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("2件以上", result.stderr)

    def test_not_applicable_candidate_cannot_block(self) -> None:
        manifest = valid_manifest()
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "invalid",
                "gate_effect": "blocks",
                "routing": "not-applicable",
                "review_unit_ids": ["R1"],
                "reason": "general hardening",
            }
        ]
        result = run_validator("candidate", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("block", result.stderr)

    def test_condition_seed_cannot_be_erased_as_not_applicable(self) -> None:
        scope = scope_baseline(valid_manifest())
        scope["scope_candidates"][0] = {
            "id": "S1",
            "seed_id": "SC1",
            "classification": "not-applicable",
            "reason": "claimed unrelated",
            "boundary": "public output",
        }
        result = run_validator("scope", scope)
        self.assertEqual(1, result.returncode)
        self.assertIn("must-applicable", result.stderr)

    def test_changed_surface_cannot_force_itself_applicable(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"][0]["kind"] = "changed-surface"
        result = run_validator("scope", scope_baseline(valid_manifest()), brief=brief)
        self.assertEqual(1, result.returncode)
        self.assertIn("classify-only", result.stderr)

    def test_each_handoff_seed_requires_its_own_pair(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"].append(
            {
                "id": "SH2",
                "kind": "handoff",
                "source": "second Browser handoff condition",
                "contract": "rendered output",
                "handoff_id": "H1",
                "coverage_obligation": "handoff-pair",
                "review_case_ids": ["H2-snapshot"],
            }
        )
        scope = scope_baseline(valid_manifest())
        scope["scope_candidates"].append(
            {
                "id": "S3",
                "seed_id": "SH2",
                "classification": "not-applicable",
                "reason": "claimed covered by the first seed",
                "boundary": "handoff surface",
            }
        )
        result = run_validator("scope", scope, brief=brief)
        self.assertEqual(1, result.returncode)
        self.assertIn("handoff-pair", result.stderr)

    def test_candidate_cannot_add_scope_found_during_discovery(self) -> None:
        baseline = scope_baseline(valid_manifest())
        manifest = valid_manifest()
        manifest["scope_candidates"].append(
            {
                "id": "SX",
                "seed_id": "SC1",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "path_id": "PX",
                "boundary": "public output",
                "review_case_ids": ["C1-default"],
                "added_during_discovery": True,
                "addition_reason": "found while exploring",
            }
        )
        manifest["review_units"].append(
            {
                "id": "RX",
                "scope_candidate_ids": ["SX"],
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "path_id": "PX",
                "review_case_id": "C1-default",
                "boundary": "public output",
                "status": "violated",
                "evidence_mode": "static",
                "evidence": "alternate caller",
                "guarantee": "alternate path violates C1",
                "reviewer_id": "reviewer-1",
            }
        )
        manifest["finding_candidates"] = [
            {
                "id": "FX",
                "validity": "valid",
                "gate_effect": "blocks",
                "routing": "fix-here",
                "review_unit_ids": ["RX"],
                "reason": "alternate path breaks C1",
            }
        ]
        result = run_validator(
            "candidate",
            manifest,
            baseline=baseline,
            discovery=discovery_baseline(manifest),
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("scope Gate未通過", result.stderr)

    def test_scope_rejects_duplicate_candidate_with_prose_variation(self) -> None:
        scope = scope_baseline(valid_manifest())
        duplicate = copy.deepcopy(scope["scope_candidates"][0])
        duplicate["id"] = "S1X"
        duplicate["reachable_path"] = "input   ->   output"
        scope["scope_candidates"].append(duplicate)
        result = run_validator("scope", scope)
        self.assertEqual(1, result.returncode)
        self.assertIn("重複scope候補", result.stderr)

    def test_scope_cannot_invent_a_review_case(self) -> None:
        scope = scope_baseline(valid_manifest())
        scope["scope_candidates"][0]["review_case_ids"].append("C1-clone")
        result = run_validator("scope", scope)
        self.assertEqual(1, result.returncode)
        self.assertIn("Review Briefにない確認case", result.stderr)

    def test_rescope_admits_new_path_then_discovery_requires_its_unit(self) -> None:
        initial = scope_baseline(valid_manifest())
        updated = copy.deepcopy(initial)
        updated["scope_candidates"].append(
            {
                "id": "SX",
                "seed_id": "SC1",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "path_id": "PX",
                "boundary": "public output",
                "review_case_ids": ["C1-default"],
                "added_during_discovery": True,
                "addition_reason": "found while exploring",
            }
        )
        self.assertEqual(
            0,
            run_validator("scope", updated, previous_scope=initial).returncode,
        )

        discovery = discovery_baseline(valid_manifest())
        discovery["scope_candidates"] = copy.deepcopy(updated["scope_candidates"])
        missing = run_validator("discovery", discovery, baseline=updated)
        self.assertEqual(1, missing.returncode)
        self.assertIn("SX", missing.stderr)

        discovery["review_units"].append(
            {
                "id": "RX",
                "scope_candidate_ids": ["SX"],
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "path_id": "PX",
                "review_case_id": "C1-default",
                "boundary": "public output",
                "status": "satisfied",
                "evidence_mode": "static",
                "evidence": "alternate caller and output",
                "guarantee": "C1 holds on the new path",
                "reviewer_id": "reviewer-1",
            }
        )
        passed = run_validator("discovery", discovery, baseline=updated)
        self.assertEqual(0, passed.returncode, passed.stderr)

    def test_scope_stage_rejects_candidate_only_fields(self) -> None:
        scope = scope_baseline(valid_manifest())
        scope["candidate_gate"] = "passed"
        scope["finding_candidates"] = [{"id": "F1"}]
        result = run_validator("scope", scope)
        self.assertEqual(1, result.returncode)
        self.assertIn("scope stageには置けません", result.stderr)

    def test_discovery_rejects_duplicate_review_case_with_prose_variation(self) -> None:
        discovery = discovery_baseline(valid_manifest())
        duplicate = copy.deepcopy(discovery["review_units"][0])
        duplicate["id"] = "R1X"
        duplicate["reachable_path"] = "input   ->   output"
        discovery["review_units"].append(duplicate)
        result = run_validator("discovery", discovery)
        self.assertEqual(1, result.returncode)
        self.assertIn("scope確認case", result.stderr)

    def test_discovery_stage_rejects_candidate_fields(self) -> None:
        discovery = discovery_baseline(valid_manifest())
        discovery["candidate_gate"] = "passed"
        discovery["finding_candidates"] = [{"id": "F1"}]
        result = run_validator("discovery", discovery)
        self.assertEqual(1, result.returncode)
        self.assertIn("discovery stageには置けません", result.stderr)

    def test_candidate_cannot_rewrite_discovery_status(self) -> None:
        manifest = valid_manifest()
        discovery = discovery_baseline(manifest)
        manifest["review_units"][0]["status"] = "violated"
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "valid",
                "gate_effect": "blocks",
                "routing": "fix-here",
                "review_unit_ids": ["R1"],
                "reason": "rewritten after discovery",
            }
        ]
        result = run_validator("candidate", manifest, discovery=discovery)
        self.assertEqual(1, result.returncode)
        self.assertIn("discovery完了後", result.stderr)

    def test_unverified_unit_requires_one_routing_candidate(self) -> None:
        manifest = valid_manifest()
        manifest["review_units"][0]["status"] = "unverified"
        discovery = discovery_baseline(manifest)
        result = run_validator("candidate", manifest, discovery=discovery)
        self.assertEqual(1, result.returncode)
        self.assertIn("violated/unverified", result.stderr)

    def test_duplicate_contract_decision_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["scope_candidates"][1]["path_id"] = "P1"
        manifest["scope_candidates"][2]["path_id"] = "P1"
        manifest["review_units"][1]["path_id"] = "P1"
        manifest["review_units"][0]["status"] = "unverified"
        manifest["review_units"][1]["status"] = "unverified"
        candidate = {
            "validity": "valid",
            "gate_effect": "blocks",
            "routing": "contract-decision",
            "review_unit_ids": ["R1", "R2"],
            "conflicting_contracts": ["C1", "rendered output"],
            "reachable_scenario": "same path requires incompatible outcomes",
            "reason": "current contracts conflict",
        }
        manifest["finding_candidates"] = [
            {"id": "F1", **candidate},
            {"id": "F2", **candidate},
        ]
        discovery = discovery_baseline(manifest)
        result = run_validator("candidate", manifest, discovery=discovery)
        self.assertEqual(1, result.returncode)
        self.assertIn("重複", result.stderr)

    def test_scope_baseline_candidate_cannot_be_silently_removed(self) -> None:
        baseline = scope_baseline(valid_manifest())
        manifest = valid_manifest()
        manifest["scope_candidates"] = [
            item for item in manifest["scope_candidates"] if item["id"] != "S1"
        ]
        manifest["review_units"] = []
        result = run_validator("candidate", manifest, baseline=baseline)
        self.assertEqual(1, result.returncode)
        self.assertIn("削除", result.stderr)

    def test_scope_reclassification_requires_reason_and_evidence(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"].append(
            {
                "id": "SCX",
                "kind": "changed-surface",
                "source": "changed adapter",
                "contract": "C1",
                "coverage_obligation": "classify-only",
                "review_case_ids": ["X-adapter", "X-adapter-error"],
            }
        )
        initial = scope_baseline(valid_manifest())
        initial["scope_candidates"].append(
            {
                "id": "SX",
                "seed_id": "SCX",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "adapter -> output",
                "path_id": "PX",
                "boundary": "adapter output",
                "review_case_ids": ["X-adapter", "X-adapter-error"],
            }
        )
        manifest = copy.deepcopy(initial)
        manifest["scope_candidates"][-1] = {
            "id": "SX",
            "seed_id": "SCX",
            "classification": "not-applicable",
            "reason": "claimed unrelated",
            "boundary": "adapter boundary",
            "previous_classification": "applicable",
            "reclassification_reason": "path is unreachable",
            "reclassification_evidence": "caller search",
        }
        result = run_validator(
            "scope", manifest, brief=brief, previous_scope=initial
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("scope_tombstone", result.stderr)

    def test_rescope_tombstone_must_match_observation_checkpoint(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"].append(
            {
                "id": "SCX",
                "kind": "changed-surface",
                "source": "changed adapter",
                "contract": "C1",
                "coverage_obligation": "classify-only",
                "review_case_ids": ["X-adapter", "X-adapter-error"],
            }
        )
        initial = scope_baseline(valid_manifest())
        initial["scope_candidates"].append(
            {
                "id": "SX",
                "seed_id": "SCX",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "adapter -> output",
                "path_id": "PX",
                "boundary": "adapter output",
                "review_case_ids": ["X-adapter", "X-adapter-error"],
            }
        )
        updated = copy.deepcopy(initial)
        updated["scope_candidates"][-1] = {
            "id": "SX",
            "seed_id": "SCX",
            "classification": "not-applicable",
            "reason": "path is unreachable",
            "boundary": "adapter boundary",
            "previous_classification": "applicable",
            "reclassification_reason": "consumer cannot call this path",
            "reclassification_evidence": "public caller graph",
        }
        updated["scope_tombstones"] = [
            {
                "id": "T1",
                "scope_candidate_id": "SX",
                "origin_review_unit_id": "ghost-unit",
                "origin_review_case_id": "X-adapter",
                "previous_classification": "applicable",
                "status": "violated",
                "evidence_mode": "static",
                "evidence": "counterexample",
                "guarantee": "preserves the observation",
                "reviewer_id": "ghost-reviewer",
            }
        ]
        observation = copy.deepcopy(initial)
        observation["state"] = "discovery-in-progress"
        observation["reviewers"] = [
            {"id": "reviewer-1", "status": "in-progress"}
        ]
        observation["review_units"] = [
            {
                "id": "RX",
                "scope_candidate_ids": ["SX"],
                "contract": "C1",
                "reachable_path": "adapter -> output",
                "path_id": "PX",
                "review_case_id": "X-adapter",
                "boundary": "adapter output",
                "status": "violated",
                "evidence_mode": "static",
                "evidence": "counterexample",
                "guarantee": "preserves the observation",
                "reviewer_id": "reviewer-1",
            },
            {
                "id": "RY",
                "scope_candidate_ids": ["SX"],
                "contract": "C1",
                "reachable_path": "adapter error -> output",
                "path_id": "PX",
                "review_case_id": "X-adapter-error",
                "boundary": "adapter output",
                "status": "violated",
                "evidence_mode": "static",
                "evidence": "second counterexample",
                "guarantee": "preserves the second observation",
                "reviewer_id": "reviewer-1",
            }
        ]
        missing_history = copy.deepcopy(updated)
        missing_history["scope_tombstones"][0]["origin_review_unit_id"] = "RX"
        missing_history["scope_tombstones"][0]["reviewer_id"] = "reviewer-1"
        missing_result = run_validator(
            "scope",
            missing_history,
            brief=brief,
            previous_scope=initial,
            observation=observation,
        )
        self.assertEqual(1, missing_result.returncode)
        self.assertIn("RY", missing_result.stderr)

        ghost = run_validator(
            "scope",
            updated,
            brief=brief,
            previous_scope=initial,
            observation=observation,
        )
        self.assertEqual(1, ghost.returncode)
        self.assertIn("観測checkpointにない確認単位", ghost.stderr)

        updated["scope_tombstones"][0]["origin_review_unit_id"] = "RX"
        updated["scope_tombstones"][0]["reviewer_id"] = "reviewer-1"
        updated["scope_tombstones"][0]["status"] = "satisfied"
        rewritten = run_validator(
            "scope",
            updated,
            brief=brief,
            previous_scope=initial,
            observation=observation,
        )
        self.assertEqual(1, rewritten.returncode)
        self.assertIn("status: 元の確認単位と一致しません", rewritten.stderr)

        updated["scope_tombstones"][0]["status"] = "violated"
        duplicate = copy.deepcopy(updated["scope_tombstones"][0])
        duplicate["id"] = "T2"
        updated["scope_tombstones"].append(duplicate)
        duplicated = run_validator(
            "scope",
            updated,
            brief=brief,
            previous_scope=initial,
            observation=observation,
        )
        self.assertEqual(1, duplicated.returncode)
        self.assertIn("tombstoneが重複", duplicated.stderr)

    def test_scope_reclassification_retains_tombstone_and_candidate(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"].append(
            {
                "id": "SCX",
                "kind": "changed-surface",
                "source": "changed adapter",
                "contract": "C1",
                "coverage_obligation": "classify-only",
                "review_case_ids": ["X-adapter"],
            }
        )
        initial = scope_baseline(valid_manifest())
        initial["scope_candidates"].append(
            {
                "id": "SX",
                "seed_id": "SCX",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "adapter -> output",
                "path_id": "PX",
                "boundary": "adapter output",
                "review_case_ids": ["X-adapter"],
            }
        )
        baseline = copy.deepcopy(initial)
        baseline["scope_candidates"][-1] = {
            "id": "SX",
            "seed_id": "SCX",
            "classification": "not-applicable",
            "reason": "path is unreachable",
            "boundary": "adapter boundary",
            "previous_classification": "applicable",
            "reclassification_reason": "consumer cannot call this path",
            "reclassification_evidence": "public caller graph",
        }
        baseline["scope_tombstones"] = [
            {
                "id": "T1",
                "scope_candidate_id": "SX",
                "origin_review_unit_id": "RX",
                "origin_review_case_id": "X-adapter",
                "previous_classification": "applicable",
                "status": "violated",
                "evidence_mode": "static",
                "evidence": "initial apparent counterexample",
                "guarantee": "retains the withdrawn observation",
                "reviewer_id": "reviewer-1",
            }
        ]
        observation = copy.deepcopy(initial)
        observation["state"] = "discovery-in-progress"
        observation["reviewers"] = [
            {"id": "reviewer-1", "status": "in-progress"}
        ]
        observation["review_units"] = [
            {
                "id": "RX",
                "scope_candidate_ids": ["SX"],
                "contract": "C1",
                "reachable_path": "adapter -> output",
                "path_id": "PX",
                "review_case_id": "X-adapter",
                "boundary": "adapter output",
                "status": "violated",
                "evidence_mode": "static",
                "evidence": "initial apparent counterexample",
                "guarantee": "retains the withdrawn observation",
                "reviewer_id": "reviewer-1",
            }
        ]
        self.assertEqual(
            0,
            run_validator(
                "scope",
                baseline,
                brief=brief,
                previous_scope=initial,
                observation=observation,
            ).returncode,
        )
        manifest = valid_manifest()
        manifest["scope_candidates"] = copy.deepcopy(baseline["scope_candidates"])
        manifest["scope_tombstones"] = copy.deepcopy(baseline["scope_tombstones"])
        manifest["finding_candidates"] = [
            {
                "id": "F1",
                "validity": "invalid",
                "gate_effect": "does-not-block",
                "routing": "not-applicable",
                "review_unit_ids": ["T1"],
                "reason": "unreachable from current contract",
            }
        ]
        discovery = discovery_baseline(manifest)
        result = run_validator(
            "candidate",
            manifest,
            brief=brief,
            baseline=baseline,
            discovery=discovery,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        rewritten = copy.deepcopy(manifest)
        rewritten["scope_tombstones"][0]["status"] = "satisfied"
        rewritten["finding_candidates"] = []
        rewritten_result = run_validator(
            "candidate",
            rewritten,
            brief=brief,
            baseline=baseline,
            discovery=discovery,
        )
        self.assertEqual(1, rewritten_result.returncode)
        self.assertIn("discovery完了後", rewritten_result.stderr)


if __name__ == "__main__":
    unittest.main()
