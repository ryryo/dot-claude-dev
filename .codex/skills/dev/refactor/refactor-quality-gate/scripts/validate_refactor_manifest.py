#!/usr/bin/env python3
"""Validate a refactor-quality-gate run manifest.

The manifest is deliberately a small, structural oracle.  It checks the
parts of the run contract that can be proved from JSON alone; it does not
decide whether an observation or a stated finding is true.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STAGES = {
    "scoped",
    "discovered",
    "frozen",
    "implemented",
    "reviewed",
    "complete",
    "hold",
}
STAGE_RANK = {
    "scoped": 0,
    "discovered": 1,
    "frozen": 2,
    "implemented": 3,
    "reviewed": 4,
    "complete": 5,
}
DIMENSION_CATEGORIES = {
    "architecture",
    "frontend",
    "test_portfolio",
    "performance",
    "contract",
    "integration",
}
PROBE_KINDS = {"counterexample", "direct_evidence"}
COVERAGE_ROLES = {"origin", "mechanism", "observation"}
DIMENSION_STATUSES = {"pending", "satisfied", "violated", "unconfirmed"}
ARTIFACT_CLASSES = {"surface", "excluded"}
FINDING_SEVERITIES = {"P0", "P1", "P2", "P3"}
FINDING_DISPOSITIONS = {"stop", "goal", "defer", "non_applicable"}
GOAL_KINDS = {"architecture", "frontend", "test_portfolio", "mixed"}
GOAL_OWNERS = {"main", "worker"}
GOAL_STATUSES = {"planned", "in_progress", "verified", "rejected"}
PERFORMANCE_RESULTS = {"not_applicable", "pending", "pass", "fail"}
BATCH_STATUSES = {"planned", "in_progress", "verified"}
REVIEW_KINDS = {"initial", "incremental", "recovery"}
REVIEW_CLASSIFICATIONS = {
    "fix_here",
    "later_gate",
    "contract_decision",
    "non_applicable",
}
REVIEW_CANDIDATE_STATUSES = {"open", "resolved", "carried"}
REVIEW_DECISIONS = {"pending", "GO", "NO_GO", "HOLD"}
CORRECTION_STATUSES = {"planned", "verified", "reverted"}
FORBIDDEN_FIELDS = {
    "branch",
    "branch_name",
    "commit",
    "commit_sha",
    "worktree",
    "session",
    "session_id",
}


def _is_int(value: Any) -> bool:
    """Return true for JSON integers, but not for booleans."""

    return isinstance(value, int) and not isinstance(value, bool)


def _is_trimmed_text(value: Any, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, str):
        return False
    if value != value.strip():
        return False
    return allow_empty or bool(value)


def _enum_value(value: Any, allowed: set[str]) -> bool:
    """Check an enum without allowing unhashable malformed JSON values to escape."""

    return isinstance(value, str) and value in allowed


def _require_text(
    value: Any,
    path: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> bool:
    if not isinstance(value, str):
        errors.append(f"{path}: string is required")
        return False
    if value != value.strip():
        errors.append(f"{path}: leading or trailing whitespace is not allowed")
        return False
    if not allow_empty and not value:
        errors.append(f"{path}: non-empty string is required")
        return False
    return True


def _require_id(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str):
        errors.append(f"{path}: non-empty ID string is required")
        return False
    if value != value.strip():
        errors.append(f"{path}: leading or trailing whitespace is not allowed")
        return False
    if not value:
        errors.append(f"{path}: non-empty ID string is required")
        return False
    return True


def _require_object(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path}: object is required")
        return False
    return True


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    identifiers: bool = False,
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path}: array is required")
        return []
    if not allow_empty and not value:
        errors.append(f"{path}: a non-empty array is required")
    result: list[str] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        valid = _require_id(item, item_path, errors) if identifiers else _require_text(item, item_path, errors)
        if valid:
            result.append(item)
    if len(result) != len(set(result)):
        errors.append(f"{path}: duplicate IDs are not allowed")
    return result


def _index_collection(
    value: Any,
    path: str,
    errors: list[str],
    *,
    allow_empty: bool = True,
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{path}: array is required")
        return {}
    if not allow_empty and not value:
        errors.append(f"{path}: a non-empty array is required")
    indexed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path}: object is required")
            continue
        item_id = item.get("id")
        if not _require_id(item_id, f"{item_path}.id", errors):
            continue
        if item_id in indexed:
            errors.append(f"{item_path}.id: duplicate ID: {item_id}")
            continue
        indexed[item_id] = item
    return indexed


def _check_references(
    values: list[str], known: set[str], path: str, errors: list[str]
) -> None:
    for index, value in enumerate(values):
        if value not in known:
            errors.append(f"{path}[{index}]: unknown ID: {value}")


def _reject_forbidden_fields(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_FIELDS:
                errors.append(f"{path}.{key}: forbidden identity field")
            _reject_forbidden_fields(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_fields(child, f"{path}[{index}]", errors)


def _validate_scope(
    scope: Any,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    path = "manifest.scope"
    if not _require_object(scope, path, errors):
        return {}
    _require_text(scope.get("target"), f"{path}.target", errors)
    _string_list(
        scope.get("current_contracts"),
        f"{path}.current_contracts",
        errors,
        allow_empty=False,
    )
    _string_list(
        scope.get("forbidden_changes"),
        f"{path}.forbidden_changes",
        errors,
        allow_empty=False,
    )
    _string_list(
        scope.get("verification"),
        f"{path}.verification",
        errors,
        allow_empty=False,
    )
    artifacts = _index_collection(
        scope.get("artifacts"), f"{path}.artifacts", errors, allow_empty=False
    )
    for artifact_id, artifact in artifacts.items():
        item_path = f"{path}.artifacts[{artifact_id}]"
        _require_text(artifact.get("source"), f"{item_path}.source", errors)
        classification = artifact.get("classification")
        if not _enum_value(classification, ARTIFACT_CLASSES):
            errors.append(
                f"{item_path}.classification: one of {sorted(ARTIFACT_CLASSES)} is required"
            )
        dimensions = _string_list(
            artifact.get("dimension_ids"),
            f"{item_path}.dimension_ids",
            errors,
            identifiers=True,
        )
        if classification == "surface":
            if not dimensions:
                errors.append(f"{item_path}.dimension_ids: surface needs at least one dimension")
            if "reason" in artifact:
                errors.append(f"{item_path}.reason: surface artifacts cannot have reason")
        elif classification == "excluded":
            if dimensions:
                errors.append(f"{item_path}.dimension_ids: excluded artifacts must be empty")
            _require_text(artifact.get("reason"), f"{item_path}.reason", errors)
    return artifacts


def _validate_dimensions(
    dimensions_value: Any,
    errors: list[str],
    current_contracts: set[str],
) -> dict[str, dict[str, Any]]:
    dimensions = _index_collection(
        dimensions_value, "manifest.dimensions", errors, allow_empty=False
    )
    referenced_contracts: set[str] = set()
    for dimension_id, dimension in dimensions.items():
        path = f"manifest.dimensions[{dimension_id}]"
        _require_text(dimension.get("category"), f"{path}.category", errors)
        if not _enum_value(dimension.get("category"), DIMENSION_CATEGORIES):
            errors.append(
                f"{path}.category: one of {sorted(DIMENSION_CATEGORIES)} is required"
            )
        for field in ("question", "contract", "causal_path", "stop_boundary"):
            _require_text(dimension.get(field), f"{path}.{field}", errors)
        contract = dimension.get("contract")
        if _is_trimmed_text(contract) and contract not in current_contracts:
            errors.append(f"{path}.contract: unknown scope contract: {contract}")
        elif _is_trimmed_text(contract):
            referenced_contracts.add(contract)
        probe = dimension.get("probe")
        if _require_object(probe, f"{path}.probe", errors):
            if not _enum_value(probe.get("kind"), PROBE_KINDS):
                errors.append(
                    f"{path}.probe.kind: one of {sorted(PROBE_KINDS)} is required"
                )
            _require_text(probe.get("description"), f"{path}.probe.description", errors)
        coverage_points = _index_collection(
            dimension.get("coverage_points"), f"{path}.coverage_points", errors
        )
        roles: set[str] = set()
        for point_id, point in coverage_points.items():
            point_path = f"{path}.coverage_points[{point_id}]"
            role = point.get("role")
            if not _enum_value(role, COVERAGE_ROLES):
                errors.append(
                    f"{point_path}.role: one of {sorted(COVERAGE_ROLES)} is required"
                )
            else:
                roles.add(role)
            _require_text(point.get("description"), f"{point_path}.description", errors)
        missing_roles = COVERAGE_ROLES - roles
        if missing_roles:
            errors.append(
                f"{path}.coverage_points: missing roles {sorted(missing_roles)}"
            )
        status = dimension.get("status")
        if not _enum_value(status, DIMENSION_STATUSES):
            errors.append(
                f"{path}.status: one of {sorted(DIMENSION_STATUSES)} is required"
            )
    for contract in sorted(current_contracts - referenced_contracts):
        errors.append(
            f"manifest.scope.current_contracts: contract is not referenced by any dimension: {contract}"
        )
    return dimensions


def _validate_findings(
    findings_value: Any,
    dimensions: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    findings = _index_collection(findings_value, "manifest.findings", errors)
    dimension_ids = set(dimensions)
    for finding_id, finding in findings.items():
        path = f"manifest.findings[{finding_id}]"
        finding_dimensions = _string_list(
            finding.get("dimension_ids"),
            f"{path}.dimension_ids",
            errors,
            identifiers=True,
            allow_empty=False,
        )
        _check_references(finding_dimensions, dimension_ids, f"{path}.dimension_ids", errors)
        for field in ("root_cause", "evidence", "reason"):
            _require_text(finding.get(field), f"{path}.{field}", errors)
        severity = finding.get("severity")
        if not _enum_value(severity, FINDING_SEVERITIES):
            errors.append(
                f"{path}.severity: one of {sorted(FINDING_SEVERITIES)} is required"
            )
        disposition = finding.get("disposition")
        if not _enum_value(disposition, FINDING_DISPOSITIONS):
            errors.append(
                f"{path}.disposition: one of {sorted(FINDING_DISPOSITIONS)} is required"
            )
        expected_disposition = (
            {
                "P0": "stop",
                "P1": "goal",
                "P2": "goal",
                "P3": None,
            }.get(severity)
            if isinstance(severity, str)
            else None
        )
        if expected_disposition is not None and disposition != expected_disposition:
            errors.append(
                f"{path}.disposition: {severity} findings require {expected_disposition}"
            )
        if severity == "P3" and not _enum_value(
            disposition, {"defer", "non_applicable"}
        ):
            errors.append(f"{path}.disposition: P3 findings require defer or non_applicable")
    return findings


def _validate_goals(
    goals_value: Any,
    findings: dict[str, dict[str, Any]],
    dimensions: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    goals = _index_collection(goals_value, "manifest.goals", errors)
    finding_ids = set(findings)
    test_portfolio_dimension_ids = {
        dimension_id
        for dimension_id, dimension in dimensions.items()
        if dimension.get("category") == "test_portfolio"
    }
    for goal_id, goal in goals.items():
        path = f"manifest.goals[{goal_id}]"
        goal_findings = _string_list(
            goal.get("finding_ids"),
            f"{path}.finding_ids",
            errors,
            identifiers=True,
            allow_empty=False,
        )
        _check_references(goal_findings, finding_ids, f"{path}.finding_ids", errors)
        for finding_id in goal_findings:
            finding = findings.get(finding_id)
            if finding is not None and not _enum_value(
                finding.get("severity"), {"P1", "P2"}
            ):
                errors.append(
                    f"{path}.finding_ids: only P1/P2 findings can become goals: {finding_id}"
                )
        owner = goal.get("owner")
        if not _enum_value(owner, GOAL_OWNERS):
            errors.append(f"{path}.owner: one of {sorted(GOAL_OWNERS)} is required")
        kind = goal.get("kind")
        if not _enum_value(kind, GOAL_KINDS):
            errors.append(f"{path}.kind: one of {sorted(GOAL_KINDS)} is required")
        _string_list(
            goal.get("write_scope"),
            f"{path}.write_scope",
            errors,
            allow_empty=False,
        )
        _string_list(goal.get("forbidden_scope"), f"{path}.forbidden_scope", errors)
        dependencies = _string_list(
            goal.get("depends_on"),
            f"{path}.depends_on",
            errors,
            identifiers=True,
        )
        _check_references(dependencies, set(goals), f"{path}.depends_on", errors)
        if goal_id in dependencies:
            errors.append(f"{path}.depends_on: self dependency is not allowed")
        _string_list(
            goal.get("behavior_oracles"),
            f"{path}.behavior_oracles",
            errors,
            allow_empty=False,
        )
        retained = _string_list(
            goal.get("retained_oracles"), f"{path}.retained_oracles", errors
        )
        covers_test_portfolio = any(
            isinstance(findings.get(finding_id, {}).get("dimension_ids"), list)
            and bool(
                set(findings[finding_id]["dimension_ids"])
                & test_portfolio_dimension_ids
            )
            for finding_id in goal_findings
            if finding_id in findings
        )
        if (kind == "test_portfolio" or covers_test_portfolio) and not retained:
            errors.append(
                f"{path}.retained_oracles: goals covering test_portfolio need at least one oracle"
            )
        performance_sensitive = goal.get("performance_sensitive")
        if not isinstance(performance_sensitive, bool):
            errors.append(f"{path}.performance_sensitive: boolean is required")
        _require_text(
            goal.get("measurement_plan"),
            f"{path}.measurement_plan",
            errors,
            allow_empty=True,
        )
        _require_text(
            goal.get("performance_acceptance"),
            f"{path}.performance_acceptance",
            errors,
            allow_empty=True,
        )
        performance_result = goal.get("performance_result")
        if not _enum_value(performance_result, PERFORMANCE_RESULTS):
            errors.append(
                f"{path}.performance_result: one of {sorted(PERFORMANCE_RESULTS)} is required"
            )
        if performance_sensitive is True:
            if not _is_trimmed_text(goal.get("measurement_plan")):
                errors.append(
                    f"{path}.measurement_plan: required for performance-sensitive goals"
                )
            if not _is_trimmed_text(goal.get("performance_acceptance")):
                errors.append(
                    f"{path}.performance_acceptance: required for performance-sensitive goals"
                )
            if performance_result == "not_applicable":
                errors.append(
                    f"{path}.performance_result: performance-sensitive goals cannot be not_applicable"
                )
        elif performance_sensitive is False:
            if goal.get("measurement_plan") != "":
                errors.append(
                    f"{path}.measurement_plan: must be empty for non-performance-sensitive goals"
                )
            if goal.get("performance_acceptance") != "":
                errors.append(
                    f"{path}.performance_acceptance: must be empty for non-performance-sensitive goals"
                )
            if performance_result != "not_applicable":
                errors.append(
                    f"{path}.performance_result: non-performance-sensitive goals require not_applicable"
                )
        status = goal.get("status")
        if not _enum_value(status, GOAL_STATUSES):
            errors.append(f"{path}.status: one of {sorted(GOAL_STATUSES)} is required")
        _require_text(
            goal.get("rejection_reason"),
            f"{path}.rejection_reason",
            errors,
            allow_empty=True,
        )
        restoration_oracles = _string_list(
            goal.get("restoration_oracles"),
            f"{path}.restoration_oracles",
            errors,
        )
        if status == "rejected":
            if not _is_trimmed_text(goal.get("rejection_reason")):
                errors.append(
                    f"{path}.rejection_reason: rejected goals require a reason"
                )
            if not restoration_oracles:
                errors.append(
                    f"{path}.restoration_oracles: rejected goals require restoration evidence"
                )
        else:
            if goal.get("rejection_reason") != "":
                errors.append(
                    f"{path}.rejection_reason: non-rejected goals must leave this empty"
                )
            if restoration_oracles:
                errors.append(
                    f"{path}.restoration_oracles: non-rejected goals must leave this empty"
                )
    return goals


def _validate_dependencies(
    goals: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(goal_id: str, trail: list[str]) -> None:
        if goal_id in visiting:
            cycle_start = trail.index(goal_id) if goal_id in trail else 0
            cycle = trail[cycle_start:] + [goal_id]
            errors.append(f"manifest.goals[{goal_id}].depends_on: dependency cycle: {' -> '.join(cycle)}")
            return
        if goal_id in visited:
            return
        visiting.add(goal_id)
        goal = goals[goal_id]
        dependencies = goal.get("depends_on")
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if isinstance(dependency, str) and dependency in goals:
                    visit(dependency, trail + [goal_id])
        visiting.remove(goal_id)
        visited.add(goal_id)

    for goal_id in goals:
        visit(goal_id, [])


def _validate_batches(
    batches_value: Any,
    goals: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    batches = _index_collection(batches_value, "manifest.implementation_batches", errors)
    goal_ids = set(goals)
    for batch_id, batch in batches.items():
        path = f"manifest.implementation_batches[{batch_id}]"
        batch_goals = _string_list(
            batch.get("goal_ids"),
            f"{path}.goal_ids",
            errors,
            identifiers=True,
            allow_empty=False,
        )
        _check_references(batch_goals, goal_ids, f"{path}.goal_ids", errors)
        if not _enum_value(batch.get("status"), BATCH_STATUSES):
            errors.append(f"{path}.status: one of {sorted(BATCH_STATUSES)} is required")
    return batches


def _validate_reviews(
    reviews_value: Any,
    dimensions: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, str],
]:
    reviews = _index_collection(reviews_value, "manifest.review_cycles", errors)
    dimension_ids = set(dimensions)
    candidates: dict[str, dict[str, Any]] = {}
    candidate_owners: dict[str, str] = {}
    initial_count = 0
    recovery_count = 0
    incremental_seen = False
    for review_id, review in reviews.items():
        path = f"manifest.review_cycles[{review_id}]"
        kind = review.get("kind")
        if not _enum_value(kind, REVIEW_KINDS):
            errors.append(f"{path}.kind: one of {sorted(REVIEW_KINDS)} is required")
        basis_ids = _string_list(
            review.get("basis_correction_batch_ids"),
            f"{path}.basis_correction_batch_ids",
            errors,
            identifiers=True,
        )
        recovery_of_review_id = review.get("recovery_of_review_id")
        _require_text(
            recovery_of_review_id,
            f"{path}.recovery_of_review_id",
            errors,
            allow_empty=True,
        )
        reopened = _string_list(
            review.get("reopened_dimension_ids"),
            f"{path}.reopened_dimension_ids",
            errors,
            identifiers=True,
        )
        carried = _string_list(
            review.get("carried_dimension_ids"),
            f"{path}.carried_dimension_ids",
            errors,
            identifiers=True,
        )
        _check_references(
            reopened, dimension_ids, f"{path}.reopened_dimension_ids", errors
        )
        _check_references(carried, dimension_ids, f"{path}.carried_dimension_ids", errors)
        overlap = set(reopened) & set(carried)
        if overlap:
            errors.append(f"{path}: reopened and carried overlap: {sorted(overlap)}")
        if kind == "initial":
            initial_count += 1
            if basis_ids:
                errors.append(
                    f"{path}.basis_correction_batch_ids: initial review must be empty"
                )
            if recovery_of_review_id != "":
                errors.append(
                    f"{path}.recovery_of_review_id: initial review must be empty"
                )
            if set(reopened) != dimension_ids:
                errors.append(f"{path}.reopened_dimension_ids: initial review must cover every dimension")
            if carried:
                errors.append(f"{path}.carried_dimension_ids: initial review must be empty")
        elif kind in {"incremental", "recovery"}:
            if not reopened:
                errors.append(f"{path}.reopened_dimension_ids: must not be empty")
            if set(reopened) | set(carried) != dimension_ids:
                errors.append(f"{path}: reopened and carried must cover every dimension")
            if kind == "incremental":
                if not basis_ids:
                    errors.append(
                        f"{path}.basis_correction_batch_ids: incremental review needs at least one basis correction batch"
                    )
                if recovery_of_review_id != "":
                    errors.append(
                        f"{path}.recovery_of_review_id: incremental review must be empty"
                    )
                incremental_seen = True
            else:
                if basis_ids:
                    errors.append(
                        f"{path}.basis_correction_batch_ids: recovery review must be empty"
                    )
                if not _is_trimmed_text(recovery_of_review_id):
                    errors.append(
                        f"{path}.recovery_of_review_id: recovery review needs an incremental provenance review"
                    )
                if not incremental_seen:
                    errors.append(
                        f"{path}: recovery requires a preceding incremental cycle"
                    )
        if kind == "recovery":
            recovery_count += 1
        raw_candidates = review.get("candidates")
        if not isinstance(raw_candidates, list):
            errors.append(f"{path}.candidates: array is required")
            raw_candidates = []
        for index, candidate in enumerate(raw_candidates):
            candidate_path = f"{path}.candidates[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{candidate_path}: object is required")
                continue
            candidate_id = candidate.get("id")
            if not _require_id(candidate_id, f"{candidate_path}.id", errors):
                continue
            if candidate_id in candidates:
                errors.append(f"{candidate_path}.id: duplicate ID: {candidate_id}")
                continue
            candidate_dimensions = _string_list(
                candidate.get("dimension_ids"),
                f"{candidate_path}.dimension_ids",
                errors,
                identifiers=True,
                allow_empty=False,
            )
            _check_references(
                candidate_dimensions,
                dimension_ids,
                f"{candidate_path}.dimension_ids",
                errors,
            )
            if set(candidate_dimensions) - set(reopened):
                errors.append(
                    f"{candidate_path}.dimension_ids: candidates must be in reopened dimensions"
                )
            origin = candidate.get("origin")
            if not _enum_value(
                origin, {"initial", "regression", "preexisting_miss"}
            ):
                errors.append(
                    f"{candidate_path}.origin: one of ['initial', 'preexisting_miss', 'regression'] is required"
                )
            elif kind == "initial" and origin != "initial":
                errors.append(f"{candidate_path}.origin: initial reviews require initial")
            elif kind == "incremental" and origin not in {
                "regression",
                "preexisting_miss",
            }:
                errors.append(
                    f"{candidate_path}.origin: incremental reviews require regression or preexisting_miss"
                )
            elif kind == "recovery" and origin != "preexisting_miss":
                errors.append(
                    f"{candidate_path}.origin: recovery reviews require preexisting_miss"
                )
            _require_text(candidate.get("root_cause"), f"{candidate_path}.root_cause", errors)
            if not _enum_value(candidate.get("classification"), REVIEW_CLASSIFICATIONS):
                errors.append(
                    f"{candidate_path}.classification: one of {sorted(REVIEW_CLASSIFICATIONS)} is required"
                )
            if not _enum_value(candidate.get("status"), REVIEW_CANDIDATE_STATUSES):
                errors.append(
                    f"{candidate_path}.status: one of {sorted(REVIEW_CANDIDATE_STATUSES)} is required"
                )
            candidates[candidate_id] = candidate
            candidate_owners[candidate_id] = review_id
        if not _enum_value(review.get("decision"), REVIEW_DECISIONS):
            errors.append(
                f"{path}.decision: one of {sorted(REVIEW_DECISIONS)} is required"
            )
    if reviews:
        first_review_id = next(iter(reviews))
        if reviews[first_review_id].get("kind") != "initial":
            errors.append("manifest.review_cycles: the first cycle must be initial")
        if initial_count != 1:
            errors.append("manifest.review_cycles: exactly one initial cycle is required")
    if recovery_count > 1:
        errors.append("manifest.review_cycles: recovery is allowed at most once")
    review_ids = list(reviews)
    review_positions = {review_id: index for index, review_id in enumerate(review_ids)}

    def has_preexisting_miss(review: dict[str, Any]) -> bool:
        raw_candidates = review.get("candidates")
        return isinstance(raw_candidates, list) and any(
            isinstance(candidate, dict)
            and candidate.get("origin") == "preexisting_miss"
            for candidate in raw_candidates
        )

    for review_id, review in reviews.items():
        if review.get("kind") != "recovery":
            continue
        path = f"manifest.review_cycles[{review_id}]"
        provenance = review.get("recovery_of_review_id")
        if not isinstance(provenance, str) or not provenance:
            continue
        if provenance not in reviews:
            errors.append(f"{path}.recovery_of_review_id: unknown review ID: {provenance}")
            continue
        if review_positions[provenance] >= review_positions[review_id]:
            errors.append(
                f"{path}.recovery_of_review_id: provenance must precede the recovery review"
            )
        if reviews[provenance].get("kind") != "incremental":
            errors.append(
                f"{path}.recovery_of_review_id: provenance must reference an incremental review"
            )
        if not has_preexisting_miss(reviews[provenance]):
            errors.append(
                f"{path}.recovery_of_review_id: provenance incremental must contain a preexisting_miss"
            )
        prior_miss_reviews = [
            earlier_id
            for earlier_id in review_ids[: review_positions[review_id]]
            if reviews[earlier_id].get("kind") == "incremental"
            and has_preexisting_miss(reviews[earlier_id])
        ]
        if prior_miss_reviews and provenance != prior_miss_reviews[0]:
            errors.append(
                f"{path}.recovery_of_review_id: must reference the first incremental preexisting_miss review"
            )
    return reviews, candidates, candidate_owners


def _validate_corrections(
    corrections_value: Any,
    reviews: dict[str, dict[str, Any]],
    candidates: dict[str, dict[str, Any]],
    candidate_owners: dict[str, str],
    dimensions: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    corrections = _index_collection(
        corrections_value, "manifest.correction_batches", errors
    )
    review_ids = set(reviews)
    candidate_ids = set(candidates)
    used_candidates: set[str] = set()
    used_source_reviews: set[str] = set()
    for correction_id, correction in corrections.items():
        path = f"manifest.correction_batches[{correction_id}]"
        source_reviews = _string_list(
            correction.get("source_review_ids"),
            f"{path}.source_review_ids",
            errors,
            identifiers=True,
            allow_empty=False,
        )
        _check_references(
            source_reviews, review_ids, f"{path}.source_review_ids", errors
        )
        ids = _string_list(
            correction.get("candidate_ids"),
            f"{path}.candidate_ids",
            errors,
            identifiers=True,
            allow_empty=False,
        )
        _check_references(ids, candidate_ids, f"{path}.candidate_ids", errors)
        affected_dimensions = _string_list(
            correction.get("affected_dimension_ids"),
            f"{path}.affected_dimension_ids",
            errors,
            identifiers=True,
            allow_empty=False,
        )
        _check_references(
            affected_dimensions,
            set(dimensions),
            f"{path}.affected_dimension_ids",
            errors,
        )
        expected_candidates: set[str] = set()
        valid_source_reviews = [
            source_review_id
            for source_review_id in source_reviews
            if source_review_id in reviews
        ]
        for source_review_id in valid_source_reviews:
            if source_review_id in used_source_reviews:
                errors.append(
                    f"{path}.source_review_ids: source review is split across correction batches: {source_review_id}"
                )
            used_source_reviews.add(source_review_id)
            source_candidates = reviews[source_review_id].get("candidates")
            if isinstance(source_candidates, list):
                expected_candidates.update(
                    candidate.get("id")
                    for candidate in source_candidates
                    if isinstance(candidate, dict)
                    and candidate.get("classification") == "fix_here"
                    and isinstance(candidate.get("id"), str)
                )
        if set(ids) != expected_candidates:
            errors.append(
                f"{path}.candidate_ids: source reviews must be covered as one complete fix_here batch; expected {sorted(expected_candidates)}"
            )
        for index, candidate_id in enumerate(ids):
            if candidate_id in candidates and candidate_id not in expected_candidates:
                errors.append(
                    f"{path}.candidate_ids[{index}]: candidate is not a fix_here candidate of the source review: {candidate_id}"
                )
            if candidate_id in used_candidates:
                errors.append(
                    f"{path}.candidate_ids[{index}]: candidate is already in another correction batch: {candidate_id}"
                )
            used_candidates.add(candidate_id)
            owner = candidate_owners.get(candidate_id)
            if owner not in valid_source_reviews:
                errors.append(
                    f"{path}.candidate_ids[{index}]: candidate source review does not match: {candidate_id}"
                )
            candidate_dimensions = candidates.get(candidate_id, {}).get("dimension_ids")
            if isinstance(candidate_dimensions, list) and not set(candidate_dimensions).issubset(
                set(affected_dimensions)
            ):
                errors.append(
                    f"{path}.affected_dimension_ids: candidate dimensions must be included for {candidate_id}"
                )
        if not _enum_value(correction.get("status"), CORRECTION_STATUSES):
            errors.append(
                f"{path}.status: one of {sorted(CORRECTION_STATUSES)} is required"
            )
        if correction.get("status") == "reverted":
            for candidate_id in ids:
                candidate = candidates.get(candidate_id)
                if candidate is not None and candidate.get("status") == "resolved":
                    errors.append(
                        f"{path}.candidate_ids: reverted correction candidates must remain unresolved: {candidate_id}"
                    )
    return corrections


def _validate_review_correction_links(
    reviews: dict[str, dict[str, Any]],
    corrections: dict[str, dict[str, Any]],
    dimensions: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    correction_ids = set(corrections)
    review_ids = list(reviews)
    review_positions = {review_id: index for index, review_id in enumerate(review_ids)}
    dimension_ids = set(dimensions)
    first_miss_review_id = next(
        (
            review_id
            for review_id, review in reviews.items()
            if review.get("kind") == "incremental"
            and isinstance(review.get("candidates"), list)
            and any(
                isinstance(candidate, dict)
                and candidate.get("origin") == "preexisting_miss"
                for candidate in review["candidates"]
            )
        ),
        None,
    )
    recovery_ids = {
        review_id
        for review_id, review in reviews.items()
        if review.get("kind") == "recovery"
        and review.get("recovery_of_review_id") == first_miss_review_id
    }

    for review_id, review in reviews.items():
        if review.get("kind") != "incremental":
            continue
        path = f"manifest.review_cycles[{review_id}]"
        basis_ids = review.get("basis_correction_batch_ids")
        if not isinstance(basis_ids, list):
            continue
        for index, basis_id in enumerate(basis_ids):
            basis_path = f"{path}.basis_correction_batch_ids[{index}]"
            if not isinstance(basis_id, str):
                continue
            if basis_id not in correction_ids:
                errors.append(f"{basis_path}: unknown correction batch ID: {basis_id}")
                continue
            correction = corrections[basis_id]
            if not _enum_value(correction.get("status"), {"verified", "reverted"}):
                errors.append(
                    f"{basis_path}: basis correction must be completed as verified or reverted"
                )
            affected = correction.get("affected_dimension_ids")
            reopened = review.get("reopened_dimension_ids")
            if isinstance(affected, list) and isinstance(reopened, list):
                affected_ids = {
                    value for value in affected if isinstance(value, str)
                }
                reopened_ids = {
                    value for value in reopened if isinstance(value, str)
                }
                missing = affected_ids - reopened_ids
                if missing:
                    errors.append(
                        f"{basis_path}: all affected dimensions must be reopened: {sorted(missing)}"
                    )
            source_review_ids = correction.get("source_review_ids")
            if isinstance(source_review_ids, list):
                for source_review_id in source_review_ids:
                    if not isinstance(source_review_id, str):
                        continue
                    if (
                        source_review_id in review_positions
                        and review_positions[source_review_id]
                        >= review_positions[review_id]
                    ):
                        errors.append(
                            f"{basis_path}: source review must precede the incremental review: {source_review_id}"
                        )

    for correction_id, correction in corrections.items():
        source_review_ids = correction.get("source_review_ids")
        if not isinstance(source_review_ids, list):
            continue
        source_review_set = {
            source_review_id
            for source_review_id in source_review_ids
            if isinstance(source_review_id, str)
        }
        if first_miss_review_id in source_review_set:
            if not recovery_ids:
                errors.append(
                    f"manifest.correction_batches[{correction_id}].source_review_ids: a recovery review is required before correcting the first preexisting_miss"
                )
            elif source_review_set.isdisjoint(recovery_ids):
                errors.append(
                    f"manifest.correction_batches[{correction_id}].source_review_ids: the first preexisting_miss correction must include its recovery review"
                )
        for source_review_id in source_review_set:
            source_review = reviews.get(source_review_id)
            if source_review is None or source_review.get("kind") != "recovery":
                continue
            provenance = source_review.get("recovery_of_review_id")
            if not isinstance(provenance, str) or provenance not in source_review_set:
                errors.append(
                    f"manifest.correction_batches[{correction_id}].source_review_ids: recovery correction must include its provenance review: {provenance}"
                )


def _validate_frozen_goal_coverage(
    findings: dict[str, dict[str, Any]],
    goals: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    references: dict[str, list[str]] = {finding_id: [] for finding_id in findings}
    for goal_id, goal in goals.items():
        goal_findings = goal.get("finding_ids")
        if not isinstance(goal_findings, list):
            continue
        for finding_id in goal_findings:
            if isinstance(finding_id, str) and finding_id in references:
                references[finding_id].append(goal_id)
    for finding_id, finding in findings.items():
        severity = finding.get("severity")
        if not _enum_value(severity, {"P1", "P2"}):
            continue
        matched = references[finding_id]
        if len(matched) != 1:
            errors.append(
                f"manifest.findings[{finding_id}]: P1/P2 finding must be covered by exactly one goal; got {matched}"
            )


def _validate_implemented_coverage(
    goals: dict[str, dict[str, Any]],
    batches: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    allow_rejected: bool = False,
) -> None:
    batch_refs: dict[str, list[str]] = {goal_id: [] for goal_id in goals}
    batch_positions = {
        batch_id: index for index, batch_id in enumerate(batches)
    }
    for batch_id, batch in batches.items():
        goal_ids = batch.get("goal_ids")
        if not isinstance(goal_ids, list):
            continue
        for goal_id in goal_ids:
            if isinstance(goal_id, str) and goal_id in batch_refs:
                batch_refs[goal_id].append(batch_id)
    for goal_id, goal in goals.items():
        status = goal.get("status")
        allowed_statuses = {"verified", "rejected"} if allow_rejected else {"verified"}
        if status not in allowed_statuses:
            expected = "verified or restoration-backed rejected" if allow_rejected else "verified"
            errors.append(
                f"manifest.goals[{goal_id}].status: implemented stages require {expected}"
            )
        if (
            goal.get("performance_sensitive") is True
            and status != "rejected"
            and goal.get("performance_result") != "pass"
        ):
            errors.append(
                f"manifest.goals[{goal_id}].performance_result: implemented stages require pass"
            )
        matched = batch_refs[goal_id]
        verified = [
            batch_id
            for batch_id in matched
            if batches[batch_id].get("status") == "verified"
        ]
        if len(verified) != 1 or len(matched) != 1:
            errors.append(
                f"manifest.goals[{goal_id}]: must be in exactly one verified batch; got {matched}"
            )
    for goal_id, goal in goals.items():
        matched = batch_refs[goal_id]
        if len(matched) != 1:
            continue
        goal_batch_position = batch_positions[matched[0]]
        dependencies = goal.get("depends_on")
        if not isinstance(dependencies, list):
            continue
        for dependency_id in dependencies:
            if not isinstance(dependency_id, str) or dependency_id not in batch_refs:
                continue
            dependency_batches = batch_refs[dependency_id]
            if len(dependency_batches) != 1:
                continue
            if batch_positions[dependency_batches[0]] >= goal_batch_position:
                errors.append(
                    f"manifest.goals[{goal_id}].depends_on: dependency {dependency_id} must be completed in an earlier batch"
                )


def _validate_stage(
    stage: Any,
    dimensions: dict[str, dict[str, Any]],
    findings: dict[str, dict[str, Any]],
    goals: dict[str, dict[str, Any]],
    batches: dict[str, dict[str, Any]],
    reviews: dict[str, dict[str, Any]],
    candidates: dict[str, dict[str, Any]],
    corrections: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if not _enum_value(stage, STAGES):
        errors.append(f"manifest.stage: one of {sorted(STAGES)} is required")
        return
    rank = STAGE_RANK.get(stage, -1)
    has_review_history = bool(reviews)
    rejected_goal_ids = {
        goal_id for goal_id, goal in goals.items() if goal.get("status") == "rejected"
    }
    if rejected_goal_ids and not (stage == "hold" and has_review_history):
        errors.append(
            "manifest.goals: rejected goals are allowed only in a reviewed HOLD"
        )
    if stage == "hold" and has_review_history:
        for dimension_id, dimension in dimensions.items():
            if not _enum_value(dimension.get("status"), {"satisfied", "violated"}):
                errors.append(
                    f"manifest.dimensions[{dimension_id}].status: reviewed hold requires satisfied or violated"
                )
        for finding_id, finding in findings.items():
            if finding.get("severity") == "P0":
                errors.append(
                    f"manifest.findings[{finding_id}]: reviewed hold cannot retain P0"
                )
        _validate_frozen_goal_coverage(findings, goals, errors)
        _validate_implemented_coverage(
            goals, batches, errors, allow_rejected=True
        )
        latest_id = next(reversed(reviews))
        if reviews[latest_id].get("decision") != "HOLD":
            errors.append("manifest.review_cycles: reviewed hold requires latest decision HOLD")
        for candidate_id, candidate in candidates.items():
            if (
                candidate.get("origin") == "regression"
                and candidate.get("status") != "resolved"
            ):
                errors.append(
                    f"manifest.review candidate {candidate_id}: reviewed hold cannot retain an unresolved regression"
                )
        if rejected_goal_ids and not any(
            candidate.get("origin") == "regression"
            and candidate.get("status") == "resolved"
            for candidate in candidates.values()
        ):
            errors.append(
                "manifest.goals: reviewed HOLD with a rejected goal requires a resolved regression candidate"
            )
    if stage != "hold" and rank >= STAGE_RANK["discovered"]:
        for dimension_id, dimension in dimensions.items():
            status = dimension.get("status")
            if status == "pending":
                errors.append(f"manifest.dimensions[{dimension_id}].status: discovered stages require an audit result")
            if status == "unconfirmed":
                errors.append(f"manifest.dimensions[{dimension_id}].status: unconfirmed requires hold stage")
    if stage != "hold" and rank >= STAGE_RANK["frozen"]:
        for dimension_id, dimension in dimensions.items():
            if not _enum_value(dimension.get("status"), {"satisfied", "violated"}):
                errors.append(f"manifest.dimensions[{dimension_id}].status: frozen stages require satisfied or violated")
        for finding_id, finding in findings.items():
            if finding.get("severity") == "P0":
                errors.append(f"manifest.findings[{finding_id}]: P0 prevents frozen or later stages")
        _validate_frozen_goal_coverage(findings, goals, errors)
        if stage == "frozen":
            for goal_id, goal in goals.items():
                if (
                    goal.get("performance_sensitive") is True
                    and goal.get("performance_result") != "pending"
                ):
                    errors.append(
                        f"manifest.goals[{goal_id}].performance_result: frozen sensitive goals require pending"
                    )
    if stage != "hold" and rank >= STAGE_RANK["implemented"]:
        _validate_implemented_coverage(goals, batches, errors)
    if rank >= STAGE_RANK["reviewed"] and not reviews:
        errors.append("manifest.review_cycles: reviewed stages require at least one cycle")
    if rank >= STAGE_RANK["reviewed"] and reviews:
        latest_id = next(reversed(reviews))
        if reviews[latest_id].get("decision") == "pending":
            errors.append("manifest.review_cycles: latest review cannot be pending")
        if reviews[latest_id].get("decision") == "GO":
            included_verified: set[str] = set()
            for correction in corrections.values():
                if correction.get("status") != "verified":
                    continue
                ids = correction.get("candidate_ids")
                if isinstance(ids, list):
                    included_verified.update(
                        candidate_id
                        for candidate_id in ids
                        if isinstance(candidate_id, str)
                    )
            for candidate_id, candidate in candidates.items():
                if candidate.get("classification") == "fix_here":
                    if candidate.get("status") != "resolved":
                        errors.append(
                            f"manifest.review candidate {candidate_id}: GO requires resolved fix_here"
                        )
                    if candidate_id not in included_verified:
                        errors.append(
                            f"manifest.review candidate {candidate_id}: GO requires a verified correction batch"
                        )
                if (
                    candidate.get("classification") == "contract_decision"
                    and candidate.get("status") != "resolved"
                ):
                    errors.append(
                        f"manifest.review candidate {candidate_id}: GO cannot retain unresolved contract_decision"
                    )
    latest_decision = (
        reviews[next(reversed(reviews))].get("decision") if reviews else None
    )
    terminal_review = (
        stage == "complete"
        or (stage == "reviewed" and latest_decision == "GO")
        or (stage == "hold" and has_review_history)
    )
    if terminal_review:
        consumed_corrections = {
            correction_id
            for review in reviews.values()
            if review.get("kind") == "incremental"
            and isinstance(review.get("basis_correction_batch_ids"), list)
            for correction_id in review["basis_correction_batch_ids"]
            if isinstance(correction_id, str)
        }
        for correction_id, correction in corrections.items():
            if (
                correction.get("status") in {"verified", "reverted"}
                and correction_id not in consumed_corrections
            ):
                errors.append(
                    f"manifest.correction_batches[{correction_id}]: completed correction requires a later incremental review before a terminal decision"
                )
        first_miss_review_id = next(
            (
                review_id
                for review_id, review in reviews.items()
                if review.get("kind") == "incremental"
                and isinstance(review.get("candidates"), list)
                and any(
                    isinstance(candidate, dict)
                    and candidate.get("origin") == "preexisting_miss"
                    for candidate in review["candidates"]
                )
            ),
            None,
        )
        if first_miss_review_id is not None and not any(
            review.get("kind") == "recovery"
            and review.get("recovery_of_review_id") == first_miss_review_id
            for review in reviews.values()
        ):
            errors.append(
                "manifest.review_cycles: the first preexisting_miss requires one recovery review before a terminal decision"
            )
    recovery_positions = [
        index
        for index, review in enumerate(reviews.values())
        if review.get("kind") == "recovery"
    ]
    if recovery_positions:
        recovery_position = recovery_positions[0]
        review_list = list(reviews.values())
        post_recovery_miss = any(
            isinstance(review.get("candidates"), list)
            and any(
                isinstance(candidate, dict)
                and candidate.get("origin") == "preexisting_miss"
                for candidate in review.get("candidates", [])
            )
            for review in review_list[recovery_position + 1 :]
        )
        if post_recovery_miss:
            latest_id = next(reversed(reviews))
            if stage != "hold":
                errors.append(
                    "manifest: recovery-after preexisting_miss requires hold stage"
                )
            if reviews[latest_id].get("decision") != "HOLD":
                errors.append(
                    "manifest: recovery-after preexisting_miss requires latest decision HOLD"
                )
    if stage == "complete":
        if not reviews:
            return
        latest_id = next(reversed(reviews))
        if reviews[latest_id].get("decision") != "GO":
            errors.append("manifest.review_cycles: latest review must be GO for complete stage")
        fix_here = {
            candidate_id
            for candidate_id, candidate in candidates.items()
            if candidate.get("classification") == "fix_here"
        }
        included_verified: set[str] = set()
        for correction in corrections.values():
            if correction.get("status") != "verified":
                continue
            ids = correction.get("candidate_ids")
            if isinstance(ids, list):
                included_verified.update(
                    candidate_id for candidate_id in ids if isinstance(candidate_id, str)
                )
        for candidate_id in sorted(fix_here):
            candidate = candidates[candidate_id]
            if candidate.get("status") != "resolved":
                errors.append(
                    f"manifest.review candidate {candidate_id}: complete requires resolved fix_here"
                )
            if candidate_id not in included_verified:
                errors.append(
                    f"manifest.review candidate {candidate_id}: complete requires a verified correction batch"
                )
        for candidate_id, candidate in candidates.items():
            if (
                candidate.get("classification") == "contract_decision"
                and candidate.get("status") != "resolved"
            ):
                errors.append(
                    f"manifest.review candidate {candidate_id}: unresolved contract_decision prevents complete"
                )


def validate_manifest(manifest: Any) -> list[str]:
    """Return contract violations for *manifest*; an empty list means valid."""

    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest: root object is required"]
    _reject_forbidden_fields(manifest, "manifest", errors)

    version = manifest.get("version")
    if not _is_int(version) or version != 1:
        errors.append("manifest.version: integer 1 is required")
    _require_id(manifest.get("run_id"), "manifest.run_id", errors)
    stage = manifest.get("stage")
    if not _enum_value(stage, STAGES):
        errors.append(f"manifest.stage: one of {sorted(STAGES)} is required")
    _require_text(manifest.get("hold_reason"), "manifest.hold_reason", errors, allow_empty=True)
    if stage == "hold" and not _is_trimmed_text(manifest.get("hold_reason")):
        errors.append("manifest.hold_reason: hold stage requires a non-empty reason")

    artifacts = _validate_scope(manifest.get("scope"), errors)
    scope_value = manifest.get("scope")
    current_contracts = {
        value
        for value in (scope_value.get("current_contracts", []) if isinstance(scope_value, dict) else [])
        if _is_trimmed_text(value)
    }
    dimensions = _validate_dimensions(
        manifest.get("dimensions"), errors, current_contracts
    )
    findings = _validate_findings(manifest.get("findings"), dimensions, errors)
    goals = _validate_goals(manifest.get("goals"), findings, dimensions, errors)
    _validate_dependencies(goals, errors)
    batches = _validate_batches(manifest.get("implementation_batches"), goals, errors)
    reviews, candidates, candidate_owners = _validate_reviews(
        manifest.get("review_cycles"), dimensions, errors
    )
    corrections = _validate_corrections(
        manifest.get("correction_batches"),
        reviews,
        candidates,
        candidate_owners,
        dimensions,
        errors,
    )
    _validate_review_correction_links(reviews, corrections, dimensions, errors)

    dimension_ids = set(dimensions)
    covered_dimensions: set[str] = set()
    surface_artifacts = 0
    for artifact_id, artifact in artifacts.items():
        if artifact.get("classification") != "surface":
            continue
        surface_artifacts += 1
        dimensions_for_artifact = artifact.get("dimension_ids")
        if isinstance(dimensions_for_artifact, list):
            valid_ids = {
                value
                for value in dimensions_for_artifact
                if isinstance(value, str) and value in dimension_ids
            }
            covered_dimensions.update(valid_ids)
            _check_references(
                [value for value in dimensions_for_artifact if isinstance(value, str)],
                dimension_ids,
                f"manifest.scope.artifacts[{artifact_id}].dimension_ids",
                errors,
            )
    if dimension_ids and surface_artifacts == 0:
        errors.append("manifest.scope.artifacts: at least one surface artifact is required")
    missing_dimensions = dimension_ids - covered_dimensions
    if missing_dimensions:
        errors.append(
            f"manifest.scope.artifacts: dimensions lack surface artifact coverage: {sorted(missing_dimensions)}"
        )

    _validate_stage(
        stage,
        dimensions,
        findings,
        goals,
        batches,
        reviews,
        candidates,
        corrections,
        errors,
    )
    return errors


def validate(manifest: Any) -> list[str]:
    """Compatibility alias for callers that use the shorter function name."""

    return validate_manifest(manifest)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a refactor quality manifest")
    parser.add_argument("manifest", help="manifest JSON path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"ERROR: {manifest_path}: {error}", file=sys.stderr)
        return 1
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {manifest['run_id']} ({manifest['stage']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
