#!/usr/bin/env python3
"""Behavior tests for the refactor-quality-gate manifest validator."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

SCRIPT_DIRECTORY = str(Path(__file__).resolve().parent)
if SCRIPT_DIRECTORY not in sys.path:
    sys.path.insert(0, SCRIPT_DIRECTORY)

from validate_refactor_manifest import validate_manifest


SCRIPT = Path(__file__).with_name("validate_refactor_manifest.py")


def coverage_points(dimension_id: str) -> list[dict[str, str]]:
    return [
        {
            "id": f"{dimension_id}-origin",
            "role": "origin",
            "description": "入力から契約の入口",
        },
        {
            "id": f"{dimension_id}-mechanism",
            "role": "mechanism",
            "description": "実装上の処理と状態",
        },
        {
            "id": f"{dimension_id}-observation",
            "role": "observation",
            "description": "利用側から見える結果",
        },
    ]


def dimension(
    dimension_id: str = "D-state",
    *,
    status: str = "pending",
    category: str = "architecture",
) -> dict[str, Any]:
    return {
        "id": dimension_id,
        "category": category,
        "question": "canonical stateのwriterは一つか",
        "contract": "selection behavior",
        "causal_path": "input -> command -> store -> selector -> UI",
        "stop_boundary": "Editor providerの公開consumerまで",
        "probe": {
            "kind": "counterexample",
            "description": "stale commandが現在selectionを上書きしない",
        },
        "coverage_points": coverage_points(dimension_id),
        "status": status,
    }


def artifact(artifact_id: str = "A-editor", dimension_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "source": "src/editor",
        "classification": "surface",
        "dimension_ids": dimension_ids or ["D-state"],
    }


def finding(
    finding_id: str = "F-state",
    *,
    severity: str = "P2",
    dimension_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "dimension_ids": dimension_ids or ["D-state"],
        "severity": severity,
        "root_cause": "selectionのwriterが重複する",
        "evidence": "到達経路と反例を確認した",
        "disposition": "goal" if severity in {"P1", "P2"} else "defer",
        "reason": "挙動維持の最小修正で解消できる",
    }


def goal(
    goal_id: str = "G-state",
    *,
    finding_ids: list[str] | None = None,
    kind: str = "architecture",
    status: str = "planned",
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": goal_id,
        "kind": kind,
        "finding_ids": finding_ids or ["F-state"],
        "owner": "main",
        "write_scope": ["src/editor/state"],
        "forbidden_scope": ["public API"],
        "depends_on": depends_on or [],
        "behavior_oracles": ["selection behavior test"],
        "retained_oracles": [],
        "performance_sensitive": False,
        "measurement_plan": "",
        "performance_acceptance": "",
        "performance_result": "not_applicable",
        "status": status,
        "rejection_reason": "",
        "restoration_oracles": [],
    }


def initial_review(
    *,
    review_id: str = "R-initial",
    reopened: list[str] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    decision: str = "GO",
) -> dict[str, Any]:
    return {
        "id": review_id,
        "kind": "initial",
        "reopened_dimension_ids": reopened or ["D-state"],
        "carried_dimension_ids": [],
        "basis_correction_batch_ids": [],
        "recovery_of_review_id": "",
        "candidates": candidates or [],
        "decision": decision,
    }


def incremental_review(
    *,
    review_id: str = "R-incremental",
    reopened: list[str] | None = None,
    carried: list[str] | None = None,
    basis: list[str] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    decision: str = "GO",
) -> dict[str, Any]:
    return {
        "id": review_id,
        "kind": "incremental",
        "reopened_dimension_ids": reopened or ["D-state"],
        "carried_dimension_ids": carried or [],
        "basis_correction_batch_ids": basis or ["C-initial"],
        "recovery_of_review_id": "",
        "candidates": candidates or [],
        "decision": decision,
    }


def recovery_review(
    *,
    review_id: str = "R-recovery",
    provenance: str = "R-incremental",
    reopened: list[str] | None = None,
    carried: list[str] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    decision: str = "GO",
) -> dict[str, Any]:
    return {
        "id": review_id,
        "kind": "recovery",
        "reopened_dimension_ids": reopened or ["D-state"],
        "carried_dimension_ids": carried or [],
        "basis_correction_batch_ids": [],
        "recovery_of_review_id": provenance,
        "candidates": candidates or [],
        "decision": decision,
    }


def review_candidate(
    candidate_id: str,
    *,
    dimension_ids: list[str] | None = None,
    classification: str = "fix_here",
    origin: str = "initial",
    status: str = "open",
) -> dict[str, Any]:
    return {
        "id": candidate_id,
        "dimension_ids": dimension_ids or ["D-state"],
        "classification": classification,
        "origin": origin,
        "root_cause": "cleanup order is reversed",
        "status": status,
    }


def correction(
    correction_id: str,
    *,
    source_review_ids: list[str],
    candidate_ids: list[str],
    affected_dimension_ids: list[str],
    status: str = "verified",
) -> dict[str, Any]:
    return {
        "id": correction_id,
        "source_review_ids": source_review_ids,
        "candidate_ids": candidate_ids,
        "affected_dimension_ids": affected_dimension_ids,
        "status": status,
    }


def two_dimension_manifest() -> dict[str, Any]:
    manifest = valid_manifest("reviewed")
    manifest["dimensions"].append(dimension("D-render", status="satisfied"))
    manifest["scope"]["artifacts"].append(artifact("A-render", ["D-render"]))
    initial_candidate = review_candidate(
        "RC-initial", origin="initial", status="resolved"
    )
    manifest["review_cycles"] = [
        initial_review(
            reopened=["D-state", "D-render"], candidates=[initial_candidate]
        ),
        incremental_review(
            reopened=["D-state"],
            carried=["D-render"],
            candidates=[],
        ),
    ]
    manifest["correction_batches"] = [
        correction(
            "C-initial",
            source_review_ids=["R-initial"],
            candidate_ids=["RC-initial"],
            affected_dimension_ids=["D-state"],
        )
    ]
    return manifest


def recovered_manifest() -> dict[str, Any]:
    manifest = two_dimension_manifest()
    miss = review_candidate(
        "RC-miss", origin="preexisting_miss", status="resolved"
    )
    recovered = review_candidate(
        "RC-recovered", origin="preexisting_miss", status="resolved"
    )
    manifest["review_cycles"][1]["candidates"] = [miss]
    manifest["review_cycles"][1]["decision"] = "NO_GO"
    manifest["review_cycles"].append(
        recovery_review(
            candidates=[recovered],
            reopened=["D-state"],
            carried=["D-render"],
            decision="NO_GO",
        )
    )
    manifest["correction_batches"].append(
        correction(
            "C-recovery",
            source_review_ids=["R-incremental", "R-recovery"],
            candidate_ids=["RC-miss", "RC-recovered"],
            affected_dimension_ids=["D-state"],
        )
    )
    manifest["review_cycles"].append(
        incremental_review(
            review_id="R-after-recovery",
            reopened=["D-state"],
            carried=["D-render"],
            basis=["C-recovery"],
        )
    )
    return manifest


def valid_manifest(stage: str = "scoped") -> dict[str, Any]:
    value: dict[str, Any] = {
        "version": 1,
        "run_id": "editor-refactor-quality",
        "stage": stage,
        "hold_reason": "",
        "scope": {
            "target": "editor state boundary",
            "current_contracts": ["selection behavior"],
            "forbidden_changes": ["public behavior"],
            "verification": ["focused test", "full test"],
            "artifacts": [artifact()],
        },
        "dimensions": [dimension(status="pending" if stage == "scoped" else "satisfied")],
        "findings": [],
        "goals": [],
        "implementation_batches": [],
        "review_cycles": [],
        "correction_batches": [],
    }
    if stage in {"frozen", "implemented", "reviewed", "complete"}:
        value["findings"] = [finding()]
        value["goals"] = [goal(status="verified" if stage in {"implemented", "reviewed", "complete"} else "planned")]
    if stage in {"implemented", "reviewed", "complete"}:
        value["implementation_batches"] = [
            {"id": "B-state", "goal_ids": ["G-state"], "status": "verified"}
        ]
    if stage in {"reviewed", "complete"}:
        value["review_cycles"] = [initial_review()]
    return value


class ValidateRefactorManifestTests(unittest.TestCase):
    def assert_valid(self, manifest: dict[str, Any]) -> None:
        self.assertEqual([], validate_manifest(manifest))

    def assert_invalid(self, manifest: dict[str, Any], text: str) -> None:
        errors = validate_manifest(manifest)
        self.assertTrue(errors, manifest)
        self.assertTrue(any(text in error for error in errors), errors)

    def test_valid_scoped_manifest(self) -> None:
        self.assert_valid(valid_manifest("scoped"))

    def test_valid_frozen_manifest(self) -> None:
        self.assert_valid(valid_manifest("frozen"))

    def test_valid_complete_manifest(self) -> None:
        self.assert_valid(valid_manifest("complete"))

    def test_duplicate_collection_id_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["dimensions"].append(copy.deepcopy(manifest["dimensions"][0]))
        self.assert_invalid(manifest, "duplicate ID")

    def test_every_dimension_needs_surface_artifact_coverage(self) -> None:
        manifest = valid_manifest()
        manifest["dimensions"].append(dimension("D-uncovered"))
        self.assert_invalid(manifest, "lack surface artifact coverage")

    def test_scope_collections_and_dimensions_are_non_empty(self) -> None:
        for field in ("current_contracts", "forbidden_changes", "verification", "artifacts"):
            with self.subTest(field=field):
                manifest = valid_manifest()
                manifest["scope"][field] = []
                self.assert_invalid(manifest, "non-empty")
        manifest = valid_manifest()
        manifest["dimensions"] = []
        self.assert_invalid(manifest, "manifest.dimensions")

    def test_dimension_contracts_must_match_and_cover_scope_contracts(self) -> None:
        manifest = valid_manifest()
        manifest["dimensions"][0]["contract"] = "unknown contract"
        self.assert_invalid(manifest, "unknown scope contract")
        manifest = valid_manifest()
        manifest["scope"]["current_contracts"].append("unreferenced contract")
        self.assert_invalid(manifest, "not referenced by any dimension")

    def test_each_dimension_needs_all_coverage_roles(self) -> None:
        manifest = valid_manifest()
        manifest["dimensions"][0]["coverage_points"] = coverage_points("D-state")[:2]
        self.assert_invalid(manifest, "missing roles")

    def test_frozen_p1_or_p2_finding_needs_exactly_one_goal(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["goals"] = []
        self.assert_invalid(manifest, "exactly one goal")

    def test_test_portfolio_goal_needs_retained_oracle(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["goals"][0]["kind"] = "test_portfolio"
        self.assert_invalid(manifest, "retained_oracles")

    def test_mixed_goal_covering_test_portfolio_needs_retained_oracle(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["dimensions"].append(
            dimension(
                "D-tests", status="satisfied", category="test_portfolio"
            )
        )
        manifest["scope"]["artifacts"].append(artifact("A-tests", ["D-tests"]))
        manifest["findings"][0]["dimension_ids"] = ["D-state", "D-tests"]
        manifest["goals"][0]["kind"] = "mixed"
        self.assert_invalid(manifest, "retained_oracles")

        manifest["goals"][0]["retained_oracles"] = [
            "behavior oracle retained after duplicate removal"
        ]
        self.assert_valid(manifest)

    def test_performance_sensitive_goal_needs_measurement_plan(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["goals"][0]["performance_sensitive"] = True
        self.assert_invalid(manifest, "measurement_plan")

    def test_frozen_sensitive_goal_accepts_pending_performance_result(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["goals"][0].update(
            {
                "performance_sensitive": True,
                "measurement_plan": "median render time on the fixed fixture",
                "performance_acceptance": "within the baseline variation",
                "performance_result": "pending",
            }
        )
        self.assert_valid(manifest)

    def test_frozen_sensitive_goal_requires_pending_result(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["goals"][0].update(
            {
                "performance_sensitive": True,
                "measurement_plan": "median render time on the fixed fixture",
                "performance_acceptance": "within the baseline variation",
                "performance_result": "fail",
            }
        )
        self.assert_invalid(manifest, "frozen sensitive goals require pending")

    def test_implemented_sensitive_goal_requires_pass_result(self) -> None:
        manifest = valid_manifest("implemented")
        manifest["goals"][0].update(
            {
                "performance_sensitive": True,
                "measurement_plan": "median render time on the fixed fixture",
                "performance_acceptance": "within the baseline variation",
                "performance_result": "fail",
            }
        )
        self.assert_invalid(manifest, "implemented stages require pass")

    def test_implemented_sensitive_goal_accepts_pass_result(self) -> None:
        manifest = valid_manifest("implemented")
        manifest["goals"][0].update(
            {
                "performance_sensitive": True,
                "measurement_plan": "median render time on the fixed fixture",
                "performance_acceptance": "within the baseline variation",
                "performance_result": "pass",
            }
        )
        self.assert_valid(manifest)

    def test_hold_without_review_history_allows_performance_failure(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["stage"] = "hold"
        manifest["hold_reason"] = "performance gate failed"
        manifest["goals"][0].update(
            {
                "performance_sensitive": True,
                "measurement_plan": "median render time on the fixed fixture",
                "performance_acceptance": "within the baseline variation",
                "performance_result": "fail",
            }
        )
        self.assert_valid(manifest)

    def test_non_performance_goal_requires_empty_measurement_fields(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["goals"][0]["measurement_plan"] = "unexpected measurement"
        self.assert_invalid(manifest, "must be empty")

    def test_goal_dependency_cycle_is_rejected(self) -> None:
        manifest = valid_manifest("frozen")
        manifest["findings"].append(finding("F-other"))
        first = goal("G-state", finding_ids=["F-state"], depends_on=["G-other"])
        second = goal("G-other", finding_ids=["F-other"], depends_on=["G-state"])
        manifest["goals"] = [first, second]
        self.assert_invalid(manifest, "dependency cycle")

    def test_goal_dependency_requires_an_earlier_verified_batch(self) -> None:
        manifest = valid_manifest("implemented")
        manifest["findings"].append(finding("F-base"))
        dependent = goal(
            "G-state",
            finding_ids=["F-state"],
            status="verified",
            depends_on=["G-base"],
        )
        dependency = goal(
            "G-base", finding_ids=["F-base"], status="verified"
        )
        manifest["goals"] = [dependent, dependency]
        manifest["implementation_batches"] = [
            {"id": "B-dependent", "goal_ids": ["G-state"], "status": "verified"},
            {"id": "B-base", "goal_ids": ["G-base"], "status": "verified"},
        ]
        self.assert_invalid(manifest, "must be completed in an earlier batch")

        manifest["implementation_batches"] = [
            {"id": "B-base", "goal_ids": ["G-base"], "status": "verified"},
            {"id": "B-dependent", "goal_ids": ["G-state"], "status": "verified"},
        ]
        self.assert_valid(manifest)

    def test_goal_dependency_cannot_share_the_same_batch(self) -> None:
        manifest = valid_manifest("implemented")
        manifest["findings"].append(finding("F-base"))
        manifest["goals"] = [
            goal(
                "G-state",
                finding_ids=["F-state"],
                status="verified",
                depends_on=["G-base"],
            ),
            goal("G-base", finding_ids=["F-base"], status="verified"),
        ]
        manifest["implementation_batches"] = [
            {
                "id": "B-shared",
                "goal_ids": ["G-base", "G-state"],
                "status": "verified",
            }
        ]
        self.assert_invalid(manifest, "must be completed in an earlier batch")

    def test_implemented_stage_needs_one_verified_batch_per_goal(self) -> None:
        manifest = valid_manifest("implemented")
        manifest["implementation_batches"] = []
        self.assert_invalid(manifest, "exactly one verified batch")

    def test_initial_review_must_reopen_every_dimension_and_carry_none(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["reopened_dimension_ids"] = []
        self.assert_invalid(manifest, "initial review must cover every dimension")

    def test_incremental_review_must_partition_every_dimension(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["dimensions"].append(dimension("D-render", status="satisfied"))
        manifest["scope"]["artifacts"].append(artifact("A-render", ["D-render"]))
        manifest["review_cycles"].append(
            {
                "id": "R-incremental",
                "kind": "incremental",
                "reopened_dimension_ids": ["D-state"],
                "carried_dimension_ids": [],
                "basis_correction_batch_ids": [],
                "recovery_of_review_id": "",
                "candidates": [],
                "decision": "GO",
            }
        )
        self.assert_invalid(manifest, "cover every dimension")

    def test_incremental_review_needs_completed_basis_correction(self) -> None:
        manifest = two_dimension_manifest()
        manifest["correction_batches"][0]["status"] = "planned"
        self.assert_invalid(manifest, "completed as verified or reverted")

    def test_incremental_basis_reopens_every_affected_dimension(self) -> None:
        manifest = two_dimension_manifest()
        manifest["review_cycles"][1]["reopened_dimension_ids"] = ["D-render"]
        manifest["review_cycles"][1]["carried_dimension_ids"] = ["D-state"]
        self.assert_invalid(manifest, "all affected dimensions must be reopened")

    def test_reverted_correction_can_be_incremental_basis(self) -> None:
        manifest = two_dimension_manifest()
        manifest["correction_batches"][0]["status"] = "reverted"
        manifest["review_cycles"][0]["candidates"][0]["status"] = "open"
        manifest["review_cycles"][1]["decision"] = "NO_GO"
        self.assert_valid(manifest)

    def test_recovery_is_allowed_only_once(self) -> None:
        manifest = valid_manifest("reviewed")
        for review_id in ("R-recovery-1", "R-recovery-2"):
            manifest["review_cycles"].append(
                {
                    "id": review_id,
                    "kind": "recovery",
                    "reopened_dimension_ids": ["D-state"],
                    "carried_dimension_ids": [],
                    "basis_correction_batch_ids": [],
                    "recovery_of_review_id": "",
                    "candidates": [],
                    "decision": "GO",
                }
            )
        self.assert_invalid(manifest, "at most once")

    def test_recovery_requires_a_preceding_incremental_cycle(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"].append(
            {
                "id": "R-recovery",
                "kind": "recovery",
                "reopened_dimension_ids": ["D-state"],
                "carried_dimension_ids": [],
                "basis_correction_batch_ids": [],
                "recovery_of_review_id": "",
                "candidates": [],
                "decision": "GO",
            }
        )
        self.assert_invalid(manifest, "preceding incremental")

    def test_recovery_requires_incremental_preexisting_miss_provenance(self) -> None:
        manifest = two_dimension_manifest()
        manifest["review_cycles"].append(
            recovery_review(
                reopened=["D-state"],
                carried=["D-render"],
                provenance="R-incremental",
            )
        )
        self.assert_invalid(manifest, "must contain a preexisting_miss")

    def test_recovery_provenance_must_reference_incremental_review(self) -> None:
        manifest = two_dimension_manifest()
        manifest["review_cycles"][1]["candidates"] = [
            review_candidate(
                "RC-miss",
                origin="preexisting_miss",
                status="open",
            )
        ]
        manifest["review_cycles"].append(
            recovery_review(
                reopened=["D-state"],
                carried=["D-render"],
                provenance="R-initial",
            )
        )
        self.assert_invalid(manifest, "must reference an incremental review")

    def test_recovery_episode_can_complete_with_one_consolidated_batch(self) -> None:
        self.assert_valid(recovered_manifest())

    def test_preexisting_miss_cannot_be_corrected_before_recovery(self) -> None:
        manifest = two_dimension_manifest()
        miss = review_candidate(
            "RC-miss", origin="preexisting_miss", status="resolved"
        )
        manifest["review_cycles"][1]["candidates"] = [miss]
        manifest["review_cycles"][1]["decision"] = "NO_GO"
        manifest["correction_batches"].append(
            correction(
                "C-miss",
                source_review_ids=["R-incremental"],
                candidate_ids=["RC-miss"],
                affected_dimension_ids=["D-state"],
            )
        )
        manifest["review_cycles"].append(
            incremental_review(
                review_id="R-after-miss",
                reopened=["D-state"],
                carried=["D-render"],
                basis=["C-miss"],
            )
        )
        manifest["stage"] = "complete"
        self.assert_invalid(manifest, "recovery review is required")

    def test_second_preexisting_miss_after_recovery_requires_hold(self) -> None:
        manifest = recovered_manifest()
        manifest["review_cycles"][-1]["candidates"] = [
            review_candidate(
                "RC-second-miss", origin="preexisting_miss", status="open"
            )
        ]
        manifest["review_cycles"][-1]["decision"] = "NO_GO"
        self.assert_invalid(manifest, "requires hold stage")

    def test_second_preexisting_miss_has_valid_reviewed_hold_shape(self) -> None:
        manifest = recovered_manifest()
        manifest["stage"] = "hold"
        manifest["hold_reason"] = "second pre-existing miss requires replanning"
        manifest["review_cycles"][-1]["candidates"] = [
            review_candidate(
                "RC-second-miss", origin="preexisting_miss", status="open"
            )
        ]
        manifest["review_cycles"][-1]["decision"] = "HOLD"
        self.assert_valid(manifest)

    def test_candidate_origin_is_constrained_by_review_kind(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["candidates"] = [
            review_candidate("RC-origin", origin="regression")
        ]
        self.assert_invalid(manifest, "initial reviews require initial")

    def test_reviewed_latest_review_cannot_be_pending(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["decision"] = "pending"
        self.assert_invalid(manifest, "latest review cannot be pending")

    def test_review_go_cannot_carry_unresolved_fix_here(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["candidates"] = [
            review_candidate("RC-open", origin="initial", status="open")
        ]
        self.assert_invalid(manifest, "GO requires resolved fix_here")

    def test_candidates_must_belong_to_reopened_dimensions(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["dimensions"].append(dimension("D-render", status="satisfied"))
        manifest["scope"]["artifacts"].append(artifact("A-render", ["D-render"]))
        manifest["review_cycles"].append(
            {
                "id": "R-incremental",
                "kind": "incremental",
                "reopened_dimension_ids": ["D-state"],
                "carried_dimension_ids": ["D-render"],
                "basis_correction_batch_ids": [],
                "recovery_of_review_id": "",
                "candidates": [
                    {
                        "id": "RC-carried",
                        "dimension_ids": ["D-render"],
                        "classification": "later_gate",
                        "origin": "regression",
                        "root_cause": "carried dimension candidate",
                        "status": "carried",
                    }
                ],
                "decision": "GO",
            }
        )
        self.assert_invalid(manifest, "candidates must be in reopened")

    def test_complete_requires_resolved_fix_here_and_verified_correction(self) -> None:
        manifest = valid_manifest("complete")
        manifest["review_cycles"][0]["candidates"] = [
            {
                "id": "RC-fix",
                "dimension_ids": ["D-state"],
                "classification": "fix_here",
                "origin": "initial",
                "root_cause": "cleanup order is reversed",
                "status": "open",
            }
        ]
        manifest["correction_batches"] = [
            {
                "id": "C-fix",
                "source_review_ids": ["R-initial"],
                "candidate_ids": ["RC-fix"],
                "affected_dimension_ids": ["D-state"],
                "status": "verified",
            }
        ]
        self.assert_invalid(manifest, "resolved fix_here")

    def test_terminal_decision_requires_incremental_review_after_correction(self) -> None:
        manifest = valid_manifest("complete")
        manifest["review_cycles"][0]["candidates"] = [
            review_candidate("RC-fix", origin="initial", status="resolved")
        ]
        manifest["correction_batches"] = [
            correction(
                "C-fix",
                source_review_ids=["R-initial"],
                candidate_ids=["RC-fix"],
                affected_dimension_ids=["D-state"],
            )
        ]
        self.assert_invalid(manifest, "requires a later incremental review")

    def test_complete_accepts_correction_after_incremental_review(self) -> None:
        manifest = two_dimension_manifest()
        manifest["stage"] = "complete"
        self.assert_valid(manifest)

    def test_correction_batch_can_reference_only_fix_here(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["candidates"] = [
            {
                "id": "RC-later",
                "dimension_ids": ["D-state"],
                "classification": "later_gate",
                "origin": "initial",
                "root_cause": "needs a later gate",
                "status": "carried",
            }
        ]
        manifest["correction_batches"] = [
            {
                "id": "C-later",
                "source_review_ids": ["R-initial"],
                "candidate_ids": ["RC-later"],
                "affected_dimension_ids": ["D-state"],
                "status": "planned",
            }
        ]
        self.assert_invalid(manifest, "not a fix_here")

    def test_correction_covers_all_fix_here_from_source_reviews(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["decision"] = "NO_GO"
        manifest["review_cycles"][0]["candidates"] = [
            review_candidate("RC-one", origin="initial"),
            review_candidate("RC-two", origin="initial"),
        ]
        manifest["correction_batches"] = [
            correction(
                "C-partial",
                source_review_ids=["R-initial"],
                candidate_ids=["RC-one"],
                affected_dimension_ids=["D-state"],
            )
        ]
        self.assert_invalid(manifest, "one complete fix_here batch")

    def test_correction_affected_dimensions_include_candidate_dimensions(self) -> None:
        manifest = two_dimension_manifest()
        manifest["correction_batches"][0]["affected_dimension_ids"] = ["D-render"]
        self.assert_invalid(manifest, "candidate dimensions must be included")

    def test_candidate_cannot_be_in_multiple_correction_batches(self) -> None:
        manifest = valid_manifest("complete")
        manifest["review_cycles"][0]["candidates"] = [
            {
                "id": "RC-fix",
                "dimension_ids": ["D-state"],
                "classification": "fix_here",
                "origin": "initial",
                "root_cause": "cleanup order is reversed",
                "status": "resolved",
            }
        ]
        manifest["correction_batches"] = [
            {
                "id": "C-fix-1",
                "source_review_ids": ["R-initial"],
                "candidate_ids": ["RC-fix"],
                "affected_dimension_ids": ["D-state"],
                "status": "verified",
            },
            {
                "id": "C-fix-2",
                "source_review_ids": ["R-initial"],
                "candidate_ids": ["RC-fix"],
                "affected_dimension_ids": ["D-state"],
                "status": "verified",
            },
        ]
        self.assert_invalid(manifest, "already in another correction batch")

    def test_source_review_cannot_be_split_across_correction_batches(self) -> None:
        manifest = valid_manifest("reviewed")
        manifest["review_cycles"][0]["decision"] = "NO_GO"
        manifest["review_cycles"][0]["candidates"] = [
            review_candidate("RC-fix", origin="initial")
        ]
        manifest["correction_batches"] = [
            correction(
                "C-first",
                source_review_ids=["R-initial"],
                candidate_ids=["RC-fix"],
                affected_dimension_ids=["D-state"],
            ),
            correction(
                "C-second",
                source_review_ids=["R-initial"],
                candidate_ids=["RC-fix"],
                affected_dimension_ids=["D-state"],
            ),
        ]
        self.assert_invalid(manifest, "source review is split")

    def test_forbidden_identity_field_is_rejected_recursively(self) -> None:
        manifest = valid_manifest()
        manifest["scope"]["metadata"] = {"nested": {"session_id": "local"}}
        self.assert_invalid(manifest, "forbidden identity field")

    def test_hold_requires_non_empty_reason(self) -> None:
        manifest = valid_manifest("hold")
        self.assert_invalid(manifest, "hold_reason")
        manifest["hold_reason"] = "P0 requires owner decision"
        self.assert_valid(manifest)

    def test_reviewed_hold_requires_completed_review_baseline(self) -> None:
        manifest = two_dimension_manifest()
        manifest["stage"] = "hold"
        manifest["hold_reason"] = "review requires replanning"
        manifest["review_cycles"][-1]["decision"] = "HOLD"
        manifest["dimensions"][0]["status"] = "pending"
        manifest["goals"][0]["status"] = "planned"
        self.assert_invalid(manifest, "reviewed hold requires satisfied or violated")
        self.assert_invalid(manifest, "implemented stages require verified")

    def test_reviewed_hold_cannot_leave_regression_open(self) -> None:
        manifest = recovered_manifest()
        manifest["stage"] = "hold"
        manifest["hold_reason"] = "second issue requires replanning"
        manifest["review_cycles"][-1]["decision"] = "HOLD"
        manifest["review_cycles"][-1]["candidates"] = [
            review_candidate("RC-regression", origin="regression", status="open")
        ]
        self.assert_invalid(manifest, "cannot retain an unresolved regression")

    def test_reviewed_hold_can_reject_a_goal_after_restoring_regression(self) -> None:
        manifest = two_dimension_manifest()
        manifest["stage"] = "hold"
        manifest["hold_reason"] = "regression forced goal rejection and replanning"
        manifest["goals"][0].update(
            {
                "status": "rejected",
                "rejection_reason": "the batch regressed selection ordering",
                "restoration_oracles": ["selection behavior restored"],
            }
        )
        manifest["review_cycles"][-1]["candidates"] = [
            review_candidate("RC-regression", origin="regression", status="resolved")
        ]
        manifest["review_cycles"][-1]["decision"] = "HOLD"
        self.assert_valid(manifest)

    def test_rejected_goal_requires_restoration_evidence(self) -> None:
        manifest = two_dimension_manifest()
        manifest["stage"] = "hold"
        manifest["hold_reason"] = "regression forced goal rejection and replanning"
        manifest["goals"][0].update(
            {
                "status": "rejected",
                "rejection_reason": "the batch regressed selection ordering",
                "restoration_oracles": [],
            }
        )
        manifest["review_cycles"][-1]["candidates"] = [
            review_candidate("RC-regression", origin="regression", status="resolved")
        ]
        manifest["review_cycles"][-1]["decision"] = "HOLD"
        self.assert_invalid(manifest, "restoration evidence")

    def test_rejected_goal_cannot_complete(self) -> None:
        manifest = valid_manifest("complete")
        manifest["goals"][0].update(
            {
                "status": "rejected",
                "rejection_reason": "the batch regressed selection ordering",
                "restoration_oracles": ["selection behavior restored"],
            }
        )
        self.assert_invalid(manifest, "only in a reviewed HOLD")

    def test_cli_reports_pass_and_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(valid_manifest("scoped")), encoding="utf-8")
            passed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, passed.returncode)
            self.assertEqual("PASS: editor-refactor-quality (scoped)\n", passed.stdout)
            self.assertEqual("", passed.stderr)

            invalid = valid_manifest("scoped")
            invalid["version"] = 2
            path.write_text(json.dumps(invalid), encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, failed.returncode)
            self.assertIn("ERROR: manifest.version:", failed.stderr)


if __name__ == "__main__":
    unittest.main()
