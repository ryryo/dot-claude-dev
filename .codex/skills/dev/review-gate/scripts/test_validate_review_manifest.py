#!/usr/bin/env python3
"""Behavior tests for the review-gate validator."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).with_name("validate_review_manifest.py")


def coverage_points(dimension_id: str) -> list[dict[str, str]]:
    return [
        {
            "id": f"{dimension_id}-origin",
            "role": "origin",
            "description": f"{dimension_id}の契約と入口",
        },
        {
            "id": f"{dimension_id}-mechanism",
            "role": "mechanism",
            "description": f"{dimension_id}の状態・resource・処理",
        },
        {
            "id": f"{dimension_id}-observation",
            "role": "observation",
            "description": f"{dimension_id}の利用側と観測結果",
        },
    ]


def valid_brief() -> dict[str, Any]:
    return {
        "review_id": "review-1",
        "review_cycle": "initial",
        "target": "US-01 Gate D",
        "gate_question": "現在契約を壊さずに成果を満たすか",
        "current_contracts": ["C-session", "C-render"],
        "handoffs": [
            {
                "id": "H-journey",
                "gate": "Journey",
                "owner": "integration",
                "contract": "C-render",
            }
        ],
        "artifact_coverage": [
            {
                "artifact_id": "A-implementation",
                "classification": "surface",
                "surface_ids": ["S-change"],
            },
            {
                "artifact_id": "A-story",
                "classification": "surface",
                "surface_ids": ["S-condition", "S-handoff"],
            },
        ],
        "catalog_check": {
            "upstream_trace": "利用者条件からproducerまで遡った",
            "downstream_trace": "変更surfaceから観測結果まで辿った",
            "independent_root_check": "異なる根本原因の不足を探索前に見直した",
        },
        "target_surfaces": [
            {
                "id": "S-condition",
                "kind": "condition",
                "source": "US-01-01",
                "contract": "C-session",
            },
            {
                "id": "S-change",
                "kind": "changed-surface",
                "source": "session adapter",
                "contract": "C-session",
            },
            {
                "id": "S-handoff",
                "kind": "handoff",
                "source": "Gate D to Journey",
                "contract": "C-render",
                "handoff_id": "H-journey",
            },
        ],
        "review_dimensions": [
            {
                "id": "D-session",
                "contract": "C-session",
                "surface_ids": ["S-condition", "S-change"],
                "causal_path": "input -> adapter -> session state",
                "stop_boundary": "shared rendererへ渡す直前まで",
                "probe": {
                    "kind": "counterexample",
                    "description": "detach失敗後に旧状態が残る操作列",
                },
                "coverage_points": coverage_points("D-session"),
            },
            {
                "id": "D-render",
                "contract": "C-render",
                "surface_ids": ["S-handoff"],
                "causal_path": "session receipt -> renderer handoff",
                "stop_boundary": "実ブラウザJourneyは後続Gate",
                "probe": {
                    "kind": "direct-evidence",
                    "description": "handoff payloadと契約テストを照合する",
                },
                "coverage_points": coverage_points("D-render"),
            },
        ],
    }


def valid_input(brief: dict[str, Any] | None = None) -> dict[str, Any]:
    brief = brief or valid_brief()
    return {
        "review_id": brief["review_id"],
        "condition_ids": [
            surface["source"]
            for surface in brief["target_surfaces"]
            if surface["kind"] == "condition"
        ],
        "current_contracts": copy.deepcopy(brief["current_contracts"]),
        "handoffs": copy.deepcopy(brief["handoffs"]),
        "target_artifacts": [
            {"id": "A-implementation", "source": "apps/web/src/session-adapter.ts"},
            {"id": "A-story", "source": "docs/USER_STORIES.md"},
        ],
    }


def rereview_brief() -> dict[str, Any]:
    brief = valid_brief()
    brief["review_cycle"] = "rereview"
    return brief


def legacy_brief(*, rereview: bool = False) -> dict[str, Any]:
    brief = valid_brief()
    brief["review_cycle"] = "rereview" if rereview else "initial"
    brief.pop("artifact_coverage")
    brief.pop("catalog_check")
    for dimension in brief["review_dimensions"]:
        dimension.pop("coverage_points")
    return brief


def remove_coverage_results(manifest: dict[str, Any]) -> None:
    for item in manifest.get("dimension_results", []):
        item.pop("coverage_results", None)


def full_scope(brief: dict[str, Any] | None = None) -> dict[str, Any]:
    brief = brief or valid_brief()
    return {
        "review_id": brief["review_id"],
        "review_mode": "full",
        "change_impacts": [],
        "state": "scope-fixed",
        "dimension_scopes": [
            {
                "dimension_id": dimension["id"],
                "classification": "applicable",
                "evidence": f"{dimension['id']}は現在の導線から到達する",
            }
            for dimension in brief["review_dimensions"]
        ],
    }


def result(
    dimension_id: str,
    *,
    status: str = "satisfied",
    source: str = "fresh",
    suffix: str = "v1",
) -> dict[str, Any]:
    value = {
        "dimension_id": dimension_id,
        "status": status,
        "evidence_mode": "executed",
        "result_source": source,
        "probe_result": f"probe {dimension_id} {suffix}",
        "evidence": f"evidence {dimension_id} {suffix}",
        "guarantee": f"guarantee {dimension_id} {suffix}",
        "reviewer_id": "reviewer-1",
        "coverage_results": [
            {
                "point_id": point["id"],
                "status": status,
                "evidence": f"{point['id']} {suffix}を確認した",
            }
            for point in coverage_points(dimension_id)
        ],
    }
    if source == "carried-forward":
        value["carry_forward_reason"] = "この観点へ届く変更がない"
    return value


def set_result_status(value: dict[str, Any], status: str) -> None:
    value["status"] = status
    for point in value["coverage_results"]:
        point["status"] = status


def discovery_from_scope(scope: dict[str, Any]) -> dict[str, Any]:
    manifest = copy.deepcopy(scope)
    manifest["state"] = "discovery-complete"
    applicable = [
        item["dimension_id"]
        for item in scope["dimension_scopes"]
        if item["classification"] == "applicable"
    ]
    manifest["dimension_results"] = [result(dimension_id) for dimension_id in applicable]
    manifest["reviewers"] = [{"id": "reviewer-1", "status": "completed"}]
    return manifest


def candidate_from_discovery(
    discovery: dict[str, Any], findings: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    manifest = copy.deepcopy(discovery)
    manifest["state"] = "candidate-sorted"
    manifest["finding_candidates"] = findings or []
    return manifest


def incremental_state(
    *, cause: str = "target-change"
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    brief = rereview_brief()
    previous = discovery_from_scope(full_scope(brief))
    impact = {
        "id": "I-1",
        "cause": cause,
        "reason": "adapter変更" if cause == "target-change" else "前回の探索不足",
        "surface_ids": ["S-change"] if cause == "target-change" else [],
        "dimension_ids": ["D-session"],
    }
    scope = full_scope(brief)
    scope["review_mode"] = "incremental"
    scope["change_impacts"] = [impact]
    current = discovery_from_scope(scope)
    current["dimension_results"] = [
        result("D-session", suffix="v2"),
        result("D-render", source="carried-forward"),
    ]
    return previous, scope, current


class ValidatorTest(unittest.TestCase):
    def run_validator(
        self,
        stage: str,
        manifest: dict[str, Any],
        *,
        brief: dict[str, Any] | None = None,
        scope: dict[str, Any] | None = None,
        discovery: dict[str, Any] | None = None,
        previous_brief: dict[str, Any] | None = None,
        previous_discovery: dict[str, Any] | None = None,
        review_input: dict[str, Any] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        brief = brief or valid_brief()
        review_input = review_input or valid_input(brief)
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)

            def write(name: str, value: dict[str, Any]) -> Path:
                path = directory / name
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                return path

            command = [
                sys.executable,
                str(SCRIPT),
                "--stage",
                stage,
                "--review-input",
                str(write("review-input.json", review_input)),
                "--brief",
                str(write("brief.json", brief)),
            ]
            if scope is not None:
                command.extend(["--scope-baseline", str(write("scope.json", scope))])
            if discovery is not None:
                command.extend(
                    ["--discovery-baseline", str(write("discovery.json", discovery))]
                )
            if previous_brief is not None:
                command.extend(
                    ["--previous-brief", str(write("previous-brief.json", previous_brief))]
                )
            if previous_discovery is not None:
                command.extend(
                    [
                        "--previous-discovery-baseline",
                        str(write("previous-discovery.json", previous_discovery)),
                    ]
                )
            command.append(str(write("manifest.json", manifest)))
            return subprocess.run(command, text=True, capture_output=True, check=False)

    def assert_passes(self, result_: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result_.returncode, 0, result_.stderr)

    def assert_fails(self, result_: subprocess.CompletedProcess[str]) -> None:
        self.assertNotEqual(result_.returncode, 0, result_.stdout)

    def test_full_review_passes_all_three_gates(self) -> None:
        brief = valid_brief()
        scope = full_scope(brief)
        discovery = discovery_from_scope(scope)
        candidate = candidate_from_discovery(discovery)
        self.assert_passes(self.run_validator("scope", scope, brief=brief))
        self.assert_passes(
            self.run_validator("discovery", discovery, brief=brief, scope=scope)
        )
        self.assert_passes(
            self.run_validator(
                "candidate", candidate, brief=brief, scope=scope, discovery=discovery
            )
        )

    def test_brief_requires_dimension_path_boundary_and_probe(self) -> None:
        for mutation in ("causal_path", "stop_boundary", "probe"):
            with self.subTest(mutation=mutation):
                brief = valid_brief()
                brief["review_dimensions"][0].pop(mutation)
                self.assert_fails(
                    self.run_validator("scope", full_scope(brief), brief=brief)
                )

    def test_initial_catalog_requires_every_target_artifact_classified_once(self) -> None:
        brief = valid_brief()
        review_input = valid_input(brief)
        brief["artifact_coverage"].pop()
        self.assert_fails(
            self.run_validator(
                "scope",
                full_scope(brief),
                brief=brief,
                review_input=review_input,
            )
        )

        brief = valid_brief()
        brief["artifact_coverage"][0] = {
            "artifact_id": "A-implementation",
            "classification": "excluded",
            "surface_ids": [],
        }
        self.assert_fails(
            self.run_validator("scope", full_scope(brief), brief=brief)
        )

    def test_initial_catalog_requires_two_direction_and_independent_root_check(self) -> None:
        for field in ("upstream_trace", "downstream_trace", "independent_root_check"):
            with self.subTest(field=field):
                brief = valid_brief()
                brief["catalog_check"][field] = ""
                self.assert_fails(
                    self.run_validator("scope", full_scope(brief), brief=brief)
                )

    def test_dimension_requires_origin_mechanism_and_observation_points(self) -> None:
        for role in ("origin", "mechanism", "observation"):
            with self.subTest(role=role):
                brief = valid_brief()
                brief["review_dimensions"][0]["coverage_points"] = [
                    point
                    for point in brief["review_dimensions"][0]["coverage_points"]
                    if point["role"] != role
                ]
                self.assert_fails(
                    self.run_validator("scope", full_scope(brief), brief=brief)
                )

    def test_discovery_cannot_skip_an_independently_owned_mechanism(self) -> None:
        brief = valid_brief()
        brief["review_dimensions"][0]["coverage_points"].append(
            {
                "id": "D-session-secondary-resource",
                "role": "mechanism",
                "description": "別ownerのdecode resourceと退役経路",
            }
        )
        scope = full_scope(brief)
        discovery = discovery_from_scope(scope)
        self.assert_fails(
            self.run_validator("discovery", discovery, brief=brief, scope=scope)
        )
        discovery["dimension_results"][0]["coverage_results"].append(
            {
                "point_id": "D-session-secondary-resource",
                "status": "satisfied",
                "evidence": "decode resourceの開始と退役を確認した",
            }
        )
        self.assert_passes(
            self.run_validator("discovery", discovery, brief=brief, scope=scope)
        )

    def test_dimension_status_must_aggregate_all_coverage_points(self) -> None:
        brief = valid_brief()
        scope = full_scope(brief)
        discovery = discovery_from_scope(scope)
        discovery["dimension_results"][0]["coverage_results"][1]["status"] = "violated"
        self.assert_fails(
            self.run_validator("discovery", discovery, brief=brief, scope=scope)
        )
        discovery["dimension_results"][0]["status"] = "violated"
        self.assert_passes(
            self.run_validator("discovery", discovery, brief=brief, scope=scope)
        )

    def test_brief_rejects_duplicate_and_whitespace_ids(self) -> None:
        for mutate in ("duplicate", "whitespace"):
            with self.subTest(mutate=mutate):
                brief = valid_brief()
                if mutate == "duplicate":
                    brief["target_surfaces"][1]["id"] = "S-condition"
                else:
                    brief["review_dimensions"][0]["surface_ids"][0] = " S-condition "
                self.assert_fails(
                    self.run_validator("scope", full_scope(brief), brief=brief)
                )

    def test_brief_rejects_unknown_contract_surface_and_handoff(self) -> None:
        mutations = (
            lambda brief: brief["review_dimensions"][0].update(contract="C-unknown"),
            lambda brief: brief["review_dimensions"][0]["surface_ids"].append("S-unknown"),
            lambda brief: brief["target_surfaces"][2].update(handoff_id="H-unknown"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                brief = valid_brief()
                mutate(brief)
                self.assert_fails(
                    self.run_validator("scope", full_scope(brief), brief=brief)
                )

    def test_every_declared_handoff_needs_a_surface_and_dimension(self) -> None:
        brief = valid_brief()
        brief["handoffs"].append(
            {
                "id": "H-uncovered",
                "gate": "Release",
                "owner": "release",
                "contract": "C-render",
            }
        )
        self.assert_fails(self.run_validator("scope", full_scope(brief), brief=brief))

    def test_brief_rejects_uncovered_surface_or_contract(self) -> None:
        for mutation in ("surface", "contract"):
            with self.subTest(mutation=mutation):
                brief = valid_brief()
                if mutation == "surface":
                    brief["review_dimensions"][0]["surface_ids"] = ["S-condition"]
                else:
                    brief["review_dimensions"] = [brief["review_dimensions"][0]]
                self.assert_fails(
                    self.run_validator("scope", full_scope(brief), brief=brief)
                )

    def test_review_input_must_match_brief_identity_conditions_contracts_and_handoffs(self) -> None:
        brief = valid_brief()
        mutations = (
            lambda item: item.update(review_id="other-review"),
            lambda item: item.update(condition_ids=["US-01-99"]),
            lambda item: item.update(current_contracts=["C-session"]),
            lambda item: item["handoffs"][0].update(owner="other-owner"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                review_input = valid_input(brief)
                mutate(review_input)
                self.assert_fails(
                    self.run_validator(
                        "scope",
                        full_scope(brief),
                        brief=brief,
                        review_input=review_input,
                    )
                )

    def test_condition_surface_source_is_the_condition_id(self) -> None:
        brief = valid_brief()
        review_input = valid_input(brief)
        brief["target_surfaces"][0]["source"] = "condition label only"
        self.assert_fails(
            self.run_validator(
                "scope",
                full_scope(brief),
                brief=brief,
                review_input=review_input,
            )
        )

    def test_changed_surface_only_dimension_may_be_not_applicable(self) -> None:
        brief = valid_brief()
        brief["review_dimensions"][0]["surface_ids"] = ["S-condition"]
        brief["review_dimensions"].append(
            {
                "id": "D-change",
                "contract": "C-session",
                "surface_ids": ["S-change"],
                "causal_path": "changed helper -> no runtime consumer",
                "stop_boundary": "import site",
                "probe": {
                    "kind": "direct-evidence",
                    "description": "全consumerを列挙する",
                },
                "coverage_points": coverage_points("D-change"),
            }
        )
        scope = full_scope(brief)
        scope["dimension_scopes"][2] = {
            "dimension_id": "D-change",
            "classification": "not-applicable",
            "evidence": "production importがない",
            "reason": "現在導線から到達しない",
        }
        self.assert_passes(self.run_validator("scope", scope, brief=brief))
        discovery = discovery_from_scope(scope)
        self.assert_passes(
            self.run_validator("discovery", discovery, brief=brief, scope=scope)
        )

    def test_contract_dimension_cannot_be_marked_not_applicable(self) -> None:
        scope = full_scope()
        scope["dimension_scopes"][0].update(
            classification="not-applicable", reason="届かない"
        )
        self.assert_fails(self.run_validator("scope", scope))

    def test_scope_requires_each_dimension_exactly_once(self) -> None:
        for mutation in ("missing", "duplicate", "unknown"):
            with self.subTest(mutation=mutation):
                scope = full_scope()
                if mutation == "missing":
                    scope["dimension_scopes"].pop()
                elif mutation == "duplicate":
                    scope["dimension_scopes"].append(
                        copy.deepcopy(scope["dimension_scopes"][0])
                    )
                else:
                    scope["dimension_scopes"][0]["dimension_id"] = "D-unknown"
                self.assert_fails(self.run_validator("scope", scope))

    def test_scope_stage_rejects_discovery_data(self) -> None:
        scope = full_scope()
        scope["dimension_results"] = []
        self.assert_fails(self.run_validator("scope", scope))

    def test_discovery_requires_every_dimension_even_after_a_violation(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        set_result_status(discovery["dimension_results"][0], "violated")
        discovery["dimension_results"].pop()
        self.assert_fails(self.run_validator("discovery", discovery, scope=scope))

    def test_discovery_rejects_duplicate_or_non_applicable_results(self) -> None:
        brief = valid_brief()
        brief["review_dimensions"][0]["surface_ids"] = ["S-condition"]
        brief["review_dimensions"].append(
            {
                "id": "D-change",
                "contract": "C-session",
                "surface_ids": ["S-change"],
                "causal_path": "helper only",
                "stop_boundary": "consumer",
                "probe": {"kind": "direct-evidence", "description": "import scan"},
                "coverage_points": coverage_points("D-change"),
            }
        )
        scope = full_scope(brief)
        scope["dimension_scopes"][2].update(
            classification="not-applicable", reason="no consumer"
        )
        base = discovery_from_scope(scope)
        duplicate = copy.deepcopy(base)
        duplicate["dimension_results"].append(
            copy.deepcopy(duplicate["dimension_results"][0])
        )
        non_applicable = copy.deepcopy(base)
        non_applicable["dimension_results"].append(result("D-change"))
        self.assert_fails(
            self.run_validator("discovery", duplicate, brief=brief, scope=scope)
        )
        self.assert_fails(
            self.run_validator("discovery", non_applicable, brief=brief, scope=scope)
        )

    def test_discovery_requires_completed_reviewer_or_valid_transfer(self) -> None:
        scope = full_scope()
        for reviewers in (
            [{"id": "reviewer-1", "status": "in-progress"}],
            [
                {
                    "id": "reviewer-1",
                    "status": "reassigned",
                    "transferred_to": "reviewer-2",
                }
            ],
        ):
            with self.subTest(reviewers=reviewers):
                discovery = discovery_from_scope(scope)
                discovery["reviewers"] = reviewers
                self.assert_fails(
                    self.run_validator("discovery", discovery, scope=scope)
                )

    def test_unverified_holds_candidate_without_a_finding_route(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        set_result_status(discovery["dimension_results"][0], "unverified")
        self.assert_passes(self.run_validator("discovery", discovery, scope=scope))
        candidate = candidate_from_discovery(discovery)
        self.assert_fails(
            self.run_validator(
                "candidate", candidate, scope=scope, discovery=discovery
            )
        )

    def test_candidate_routes_every_violation_exactly_once(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        set_result_status(discovery["dimension_results"][0], "violated")
        self.assert_fails(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery),
                scope=scope,
                discovery=discovery,
            )
        )
        finding = {
            "id": "F-1",
            "routing": "fix-here",
            "dimension_ids": ["D-session"],
            "reason": "現在契約を破る",
            "minimal_fix_boundary": "session adapter内だけを直す",
        }
        self.assert_passes(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [finding]),
                scope=scope,
                discovery=discovery,
            )
        )
        duplicate = candidate_from_discovery(
            discovery,
            [finding, {**finding, "id": "F-2", "reason": "same issue"}],
        )
        self.assert_fails(
            self.run_validator(
                "candidate", duplicate, scope=scope, discovery=discovery
            )
        )

    def test_fix_here_requires_minimal_fix_boundary(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        set_result_status(discovery["dimension_results"][0], "violated")
        finding = {
            "id": "F-1",
            "routing": "fix-here",
            "dimension_ids": ["D-session"],
            "reason": "契約違反",
        }
        self.assert_fails(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [finding]),
                scope=scope,
                discovery=discovery,
            )
        )

    def test_candidate_cannot_mutate_discovery_baseline(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        mutations = (
            lambda item: item["dimension_results"][0].update(evidence="rewritten"),
            lambda item: item["dimension_scopes"][0].update(evidence="rewritten"),
            lambda item: item["reviewers"].append(
                {"id": "reviewer-2", "status": "completed"}
            ),
            lambda item: item["change_impacts"].append(
                {
                    "id": "I-x",
                    "cause": "target-change",
                    "reason": "late",
                    "surface_ids": ["S-change"],
                    "dimension_ids": ["D-session"],
                }
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                candidate = candidate_from_discovery(discovery)
                mutate(candidate)
                self.assert_fails(
                    self.run_validator(
                        "candidate", candidate, scope=scope, discovery=discovery
                    )
                )

    def test_later_gate_requires_declared_handoff_dimension(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        valid = {
            "id": "F-later",
            "routing": "later-gate",
            "dimension_ids": ["D-render"],
            "reason": "実Journeyは後続責務",
            "handoff_id": "H-journey",
        }
        self.assert_passes(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [valid]),
                scope=scope,
                discovery=discovery,
            )
        )
        for bad_handoff, dimensions in (
            ("H-unknown", ["D-render"]),
            ("H-journey", ["D-session"]),
        ):
            finding = {**valid, "handoff_id": bad_handoff, "dimension_ids": dimensions}
            self.assert_fails(
                self.run_validator(
                    "candidate",
                    candidate_from_discovery(discovery, [finding]),
                    scope=scope,
                    discovery=discovery,
                )
            )

    def test_contract_decision_needs_a_reachable_two_contract_conflict(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        for item in discovery["dimension_results"]:
            set_result_status(item, "violated")
        finding = {
            "id": "F-contract",
            "routing": "contract-decision",
            "dimension_ids": ["D-session", "D-render"],
            "reason": "両契約を同時には満たせない",
            "conflicting_contracts": ["C-session", "C-render"],
            "reachable_scenario": "現在の保存導線で同時に発生する",
        }
        self.assert_passes(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [finding]),
                scope=scope,
                discovery=discovery,
            )
        )
        broken = copy.deepcopy(finding)
        broken["dimension_ids"] = ["D-session"]
        self.assert_fails(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [broken]),
                scope=scope,
                discovery=discovery,
            )
        )

    def test_incremental_review_reopens_only_impacted_dimensions(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, discovery = incremental_state()
        common = {
            "brief": brief,
            "previous_brief": previous_brief,
            "previous_discovery": previous,
        }
        self.assert_passes(self.run_validator("scope", scope, **common))
        self.assert_passes(
            self.run_validator("discovery", discovery, scope=scope, **common)
        )
        self.assert_passes(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery),
                scope=scope,
                discovery=discovery,
                **common,
            )
        )

    def test_incremental_requires_both_previous_baselines(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, _ = incremental_state()
        self.assert_fails(self.run_validator("scope", scope, brief=brief))
        self.assert_fails(
            self.run_validator(
                "scope", scope, brief=brief, previous_brief=previous_brief
            )
        )
        self.assert_fails(
            self.run_validator(
                "scope", scope, brief=brief, previous_discovery=previous
            )
        )

    def test_existing_legacy_review_can_finish_without_restarting(self) -> None:
        previous_brief = legacy_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        remove_coverage_results(previous)
        brief = legacy_brief(rereview=True)
        scope = full_scope(brief)
        scope["review_mode"] = "incremental"
        scope["change_impacts"] = [
            {
                "id": "I-legacy",
                "cause": "review-gap",
                "reason": "固定済み旧reviewの探索不足だけを再確認する",
                "surface_ids": [],
                "dimension_ids": ["D-session"],
            }
        ]
        discovery = discovery_from_scope(scope)
        discovery["dimension_results"] = [
            result("D-session", suffix="legacy-v2"),
            result("D-render", source="carried-forward"),
        ]
        remove_coverage_results(discovery)
        review_input = valid_input(brief)
        review_input.pop("target_artifacts")
        common = {
            "brief": brief,
            "previous_brief": previous_brief,
            "previous_discovery": previous,
            "review_input": review_input,
        }
        self.assert_passes(self.run_validator("scope", scope, **common))
        self.assert_passes(
            self.run_validator("discovery", discovery, scope=scope, **common)
        )

    def test_incremental_requires_a_semantic_change_impact(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        scope = full_scope(brief)
        scope["review_mode"] = "incremental"
        scope["change_impacts"] = []
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_full_rereview_requires_previous_baselines_and_reason(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        brief = rereview_brief()
        brief["review_dimensions"][0]["stop_boundary"] = "new boundary"
        scope = full_scope(brief)
        self.assert_fails(self.run_validator("scope", scope, brief=brief))
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )
        brief["full_review_reason"] = "停止境界の意味が変わった"
        self.assert_passes(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_incremental_rejects_catalog_or_scope_changes(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        for mutation in ("contract", "surface", "dimension", "handoff", "scope"):
            with self.subTest(mutation=mutation):
                brief = copy.deepcopy(previous_brief)
                brief["review_cycle"] = "rereview"
                scope = full_scope(brief)
                scope["review_mode"] = "incremental"
                scope["change_impacts"] = [
                    {
                        "id": "I-gap",
                        "cause": "review-gap",
                        "reason": "既存観点の探索不足",
                        "surface_ids": [],
                        "dimension_ids": ["D-session"],
                    }
                ]
                if mutation == "contract":
                    brief["current_contracts"][0] = "C-session-v2"
                    brief["target_surfaces"][0]["contract"] = "C-session-v2"
                    brief["target_surfaces"][1]["contract"] = "C-session-v2"
                    brief["review_dimensions"][0]["contract"] = "C-session-v2"
                elif mutation == "surface":
                    brief["target_surfaces"][1]["source"] = "new adapter"
                elif mutation == "dimension":
                    brief["review_dimensions"][0]["causal_path"] = "new causal path"
                elif mutation == "handoff":
                    brief["handoffs"][0]["owner"] = "new owner"
                else:
                    scope["dimension_scopes"][0].update(
                        classification="not-applicable", reason="new scope"
                    )
                self.assert_fails(
                    self.run_validator(
                        "scope",
                        scope,
                        brief=brief,
                        previous_brief=previous_brief,
                        previous_discovery=previous,
                    )
                )

    def test_incremental_cannot_replace_scope_evidence(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, _ = incremental_state()
        scope["dimension_scopes"][0]["evidence"] = "別の到達根拠へ差し替えた"
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_target_change_explains_shared_dimensions_not_reopened(self) -> None:
        previous_brief = valid_brief()
        previous_brief["review_dimensions"].append(
            {
                "id": "D-second-path",
                "contract": "C-session",
                "surface_ids": ["S-change"],
                "causal_path": "adapter -> retry queue",
                "stop_boundary": "queue consumer",
                "probe": {
                    "kind": "counterexample",
                    "description": "retry後の二重適用",
                },
                "coverage_points": coverage_points("D-second-path"),
            }
        )
        previous = discovery_from_scope(full_scope(previous_brief))
        brief = copy.deepcopy(previous_brief)
        brief["review_cycle"] = "rereview"
        scope = full_scope(brief)
        scope["review_mode"] = "incremental"
        scope["change_impacts"] = [
            {
                "id": "I-1",
                "cause": "target-change",
                "reason": "adapter変更",
                "surface_ids": ["S-change"],
                "dimension_ids": ["D-session"],
            }
        ]
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )
        scope["change_impacts"][0]["unaffected_dimensions"] = [
            {
                "dimension_id": "D-second-path",
                "unaffected_reason": "変更はretry queueへ渡す分岐より後にある",
            }
        ]
        self.assert_passes(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )
        scope["change_impacts"][0]["unaffected_dimensions"][0][
            "unaffected_reason"
        ] = ""
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_impacts_cannot_contradict_each_other(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        brief = rereview_brief()
        scope = full_scope(brief)
        scope["review_mode"] = "incremental"
        scope["change_impacts"] = [
            {
                "id": "I-change",
                "cause": "target-change",
                "reason": "adapter変更",
                "surface_ids": ["S-change"],
                "dimension_ids": ["D-session"],
            },
            {
                "id": "I-gap",
                "cause": "review-gap",
                "reason": "旧探索不足",
                "surface_ids": [],
                "dimension_ids": ["D-session"],
            },
        ]
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_impacts_reject_unknown_ids_and_unknown_causes(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        brief = rereview_brief()
        for cause, surface_ids, dimension_ids in (
            ("target-change", ["S-unknown"], ["D-session"]),
            ("review-gap", [], ["D-unknown"]),
            ("unknown-cause", [], ["D-session"]),
        ):
            with self.subTest(cause=cause):
                scope = full_scope(brief)
                scope["review_mode"] = "incremental"
                scope["change_impacts"] = [
                    {
                        "id": "I-1",
                        "cause": cause,
                        "reason": "changed",
                        "surface_ids": surface_ids,
                        "dimension_ids": dimension_ids,
                    }
                ]
                self.assert_fails(
                    self.run_validator(
                        "scope",
                        scope,
                        brief=brief,
                        previous_brief=previous_brief,
                        previous_discovery=previous,
                    )
                )

    def test_incremental_rejects_wrong_fresh_or_carry_transition(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, current = incremental_state()
        impacted_carried = copy.deepcopy(current)
        impacted_carried["dimension_results"][0] = result(
            "D-session", source="carried-forward"
        )
        unaffected_fresh = copy.deepcopy(current)
        unaffected_fresh["dimension_results"][1] = result("D-render", suffix="v2")
        changed_carry = copy.deepcopy(current)
        changed_carry["dimension_results"][1]["evidence"] = "rewritten"
        missing_reason = copy.deepcopy(current)
        missing_reason["dimension_results"][1].pop("carry_forward_reason")
        for manifest in (
            impacted_carried,
            unaffected_fresh,
            changed_carry,
            missing_reason,
        ):
            with self.subTest(manifest=manifest):
                self.assert_fails(
                    self.run_validator(
                        "discovery",
                        manifest,
                        brief=brief,
                        scope=scope,
                        previous_brief=previous_brief,
                        previous_discovery=previous,
                    )
                )

    def test_brief_wording_change_is_not_an_incremental_catalog(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        brief = copy.deepcopy(previous_brief)
        brief["review_cycle"] = "rereview"
        brief["target"] = "読みやすくした対象説明"
        brief["gate_question"] = "同じ契約を満たしているか"
        scope = full_scope(brief)
        scope["review_mode"] = "incremental"
        scope["change_impacts"] = [
            {
                "id": "I-gap",
                "cause": "review-gap",
                "reason": "既存観点の探索不足",
                "surface_ids": [],
                "dimension_ids": ["D-session"],
            }
        ]
        self.assert_fails(
            self.run_validator(
                "scope",
                scope,
                brief=brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_full_rerun_needs_catalog_or_scope_change(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        same_brief = copy.deepcopy(previous_brief)
        same_brief["review_cycle"] = "rereview"
        same_brief["full_review_reason"] = "全面探索が必要と判断した"
        self.assert_fails(
            self.run_validator(
                "scope",
                full_scope(same_brief),
                brief=same_brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )
        changed_brief = copy.deepcopy(previous_brief)
        changed_brief["review_cycle"] = "rereview"
        changed_brief["full_review_reason"] = "停止境界を意味的に変更した"
        changed_brief["review_dimensions"][0]["stop_boundary"] = "new boundary"
        self.assert_passes(
            self.run_validator(
                "scope",
                full_scope(changed_brief),
                brief=changed_brief,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_incremental_finding_origin_matches_reopened_dimension(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, discovery = incremental_state()
        set_result_status(discovery["dimension_results"][0], "violated")
        base = {
            "id": "F-1",
            "routing": "fix-here",
            "dimension_ids": ["D-session"],
            "reason": "変更により契約が壊れた",
            "minimal_fix_boundary": "adapter内だけを修正",
            "origin_evidence": "直前結果との比較で変更経路に初めて発生",
        }
        common = {
            "brief": brief,
            "scope": scope,
            "discovery": discovery,
            "previous_brief": previous_brief,
            "previous_discovery": previous,
        }
        valid = candidate_from_discovery(
            discovery, [{**base, "origin": "change-regression"}]
        )
        self.assert_passes(self.run_validator("candidate", valid, **common))
        wrong = candidate_from_discovery(
            discovery, [{**base, "origin": "prior-review-miss"}]
        )
        self.assert_fails(self.run_validator("candidate", wrong, **common))

    def test_carried_violation_keeps_its_existing_finding_without_new_origin(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, discovery = incremental_state()
        set_result_status(previous["dimension_results"][1], "violated")
        set_result_status(discovery["dimension_results"][1], "violated")
        finding = {
            "id": "F-carried",
            "routing": "fix-here",
            "dimension_ids": ["D-render"],
            "reason": "未修正の既知blocker",
            "minimal_fix_boundary": "renderer handoff境界だけを直す",
        }
        self.assert_passes(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [finding]),
                brief=brief,
                scope=scope,
                discovery=discovery,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_legacy_case_and_migration_fields_are_rejected(self) -> None:
        brief = valid_brief()
        review_input = valid_input(brief)
        scope = full_scope(brief)
        variants = []
        legacy_input = copy.deepcopy(review_input)
        legacy_input["scope_seeds"] = []
        variants.append((legacy_input, brief, scope))
        legacy_brief = copy.deepcopy(brief)
        legacy_brief["review_case_migrations"] = []
        variants.append((review_input, legacy_brief, scope))
        legacy_manifest = copy.deepcopy(scope)
        legacy_manifest["review_units"] = []
        variants.append((review_input, brief, legacy_manifest))
        for input_value, brief_value, manifest in variants:
            with self.subTest(manifest=manifest):
                self.assert_fails(
                    self.run_validator(
                        "scope",
                        manifest,
                        brief=brief_value,
                        review_input=input_value,
                    )
                )

    def test_malformed_surface_ids_fail_without_traceback(self) -> None:
        previous_brief = valid_brief()
        previous = discovery_from_scope(full_scope(previous_brief))
        brief = rereview_brief()
        brief["review_dimensions"][0]["surface_ids"] = [{"bad": 1}]
        scope = full_scope(brief)
        scope["review_mode"] = "incremental"
        scope["change_impacts"] = [
            {
                "id": "I-change",
                "cause": "target-change",
                "reason": "adapter変更",
                "surface_ids": ["S-change"],
                "dimension_ids": ["D-session"],
            }
        ]
        result_ = self.run_validator(
            "scope",
            scope,
            brief=brief,
            previous_brief=previous_brief,
            previous_discovery=previous,
        )
        self.assert_fails(result_)
        self.assertNotIn("Traceback", result_.stderr)

    def test_review_gap_finding_uses_prior_review_miss_origin(self) -> None:
        brief = rereview_brief()
        previous_brief = valid_brief()
        previous, scope, discovery = incremental_state(cause="review-gap")
        set_result_status(discovery["dimension_results"][0], "violated")
        finding = {
            "id": "F-gap",
            "routing": "fix-here",
            "dimension_ids": ["D-session"],
            "reason": "前回と同じ実装に未確認の失敗条件がある",
            "minimal_fix_boundary": "既存契約内の失敗条件だけを直す",
            "origin": "prior-review-miss",
            "origin_evidence": "変更前にも同じ反例が再現する",
        }
        self.assert_passes(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [finding]),
                brief=brief,
                scope=scope,
                discovery=discovery,
                previous_brief=previous_brief,
                previous_discovery=previous,
            )
        )

    def test_initial_full_finding_does_not_take_incremental_origin(self) -> None:
        scope = full_scope()
        discovery = discovery_from_scope(scope)
        set_result_status(discovery["dimension_results"][0], "violated")
        finding = {
            "id": "F-1",
            "routing": "fix-here",
            "dimension_ids": ["D-session"],
            "reason": "契約違反",
            "minimal_fix_boundary": "adapter内だけを修正",
            "origin": "prior-review-miss",
            "origin_evidence": "first reviewには分類できない",
        }
        self.assert_fails(
            self.run_validator(
                "candidate",
                candidate_from_discovery(discovery, [finding]),
                scope=scope,
                discovery=discovery,
            )
        )


if __name__ == "__main__":
    unittest.main()
