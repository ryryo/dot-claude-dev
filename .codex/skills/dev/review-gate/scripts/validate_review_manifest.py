#!/usr/bin/env python3
"""Validate the lightweight review-gate state machine.

The validator checks structural coverage and allowed state transitions. It
cannot judge whether the Brief lists every real surface, whether dimensions
are genuinely independent, or whether evidence is true.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SURFACE_KINDS = {"condition", "invariant", "changed-surface", "handoff"}
PROBE_KINDS = {"counterexample", "direct-evidence"}
COVERAGE_ROLES = {"origin", "mechanism", "observation"}
ARTIFACT_CLASSES = {"surface", "excluded"}
SCOPE_CLASSES = {"applicable", "not-applicable"}
REVIEW_MODES = {"full", "incremental"}
REVIEW_CYCLES = {"initial", "rereview"}
IMPACT_CAUSES = {"target-change", "review-gap"}
RESULT_STATES = {"satisfied", "violated", "unverified"}
RESULT_SOURCES = {"fresh", "carried-forward"}
EVIDENCE_MODES = {"executed", "static", "existing"}
REVIEWER_STATES = {"completed", "reassigned"}
ROUTINGS = {"fix-here", "later-gate", "contract-decision", "not-applicable"}
LEGACY_INPUT_FIELDS = {"scope_seeds", "previous_brief_digest"}
LEGACY_BRIEF_FIELDS = {"revision", "review_case_migrations", "scope_seeds"}
LEGACY_MANIFEST_FIELDS = {
    "brief_revision",
    "scope_candidates",
    "review_units",
    "scope_tombstones",
    "scope_gate",
    "discovery_gate",
    "candidate_gate",
    "observation_checkpoint",
}
LEGACY_FIELDS = LEGACY_INPUT_FIELDS | LEGACY_BRIEF_FIELDS | LEGACY_MANIFEST_FIELDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="review-gateのscope／discovery／candidateを検証する"
    )
    parser.add_argument(
        "--stage", choices=("scope", "discovery", "candidate"), required=True
    )
    parser.add_argument(
        "--review-input", required=True, help="正本から固定した最小Review Input"
    )
    parser.add_argument("--brief", required=True, help="探索前に固定したReview Brief")
    parser.add_argument(
        "--scope-baseline",
        help="scope stageで通過したmanifest。discovery/candidateでは必須",
    )
    parser.add_argument(
        "--discovery-baseline",
        help="discovery stageで通過したmanifest。candidateでは必須",
    )
    parser.add_argument(
        "--previous-brief",
        help="再レビュー前に使用したReview Brief。incrementalでは必須",
    )
    parser.add_argument(
        "--previous-discovery-baseline",
        help="再レビュー前に完了していたdiscovery manifest。incrementalでは必須",
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="-",
        help="検証するJSON。省略または-で標準入力",
    )
    return parser.parse_args()


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_object(path: str | None, label: str, errors: list[str]) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        value = load_json(path)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{label}を読めません: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}のrootはobjectである必要があります")
        return None
    return value


def text_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def identifier_value(value: Any) -> bool:
    return text_value(value) and value == value.strip()


def identifier_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if identifier_value(item)}


def reject_fields(
    item: dict[str, Any], forbidden: set[str], where: str, errors: list[str]
) -> None:
    found = sorted(forbidden & set(item))
    if found:
        errors.append(f"{where}: 廃止済みfieldは使用できません: {found}")


def require_text(item: dict[str, Any], key: str, where: str, errors: list[str]) -> None:
    if not text_value(item.get(key)):
        errors.append(f"{where}.{key}: 空でない文字列が必要です")


def require_identifier(
    item: dict[str, Any], key: str, where: str, errors: list[str]
) -> None:
    value = item.get(key)
    if not text_value(value):
        errors.append(f"{where}.{key}: 空でないIDが必要です")
    elif not identifier_value(value):
        errors.append(f"{where}.{key}: 前後空白は使用できません")


def unique_texts(
    value: Any,
    where: str,
    errors: list[str],
    *,
    allow_empty: bool,
) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        qualifier = "" if allow_empty else "空でない"
        errors.append(f"{where}: {qualifier}ID配列が必要です")
        return []
    if not all(identifier_value(item) for item in value):
        errors.append(f"{where}: 前後空白のない非空IDだけを指定してください")
        return []
    if len(set(value)) != len(value):
        errors.append(f"{where}: IDが重複しています")
    return value


def unique_objects(
    value: Any, where: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{where}: 配列が必要です")
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(value):
        location = f"{where}[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        require_identifier(raw, "id", location, errors)
        item_id = raw.get("id")
        if not identifier_value(item_id):
            continue
        if item_id in indexed:
            errors.append(f"{location}.id: 重複しています: {item_id}")
            continue
        indexed[item_id] = raw
    return indexed


def handoff_core(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate": item.get("gate"),
        "owner": item.get("owner"),
        "contract": item.get("contract"),
    }


def surface_core(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": item.get("kind"),
        "source": item.get("source"),
        "contract": item.get("contract"),
        "handoff_id": item.get("handoff_id"),
    }


def dimension_core(item: dict[str, Any]) -> dict[str, Any]:
    probe = item.get("probe") if isinstance(item.get("probe"), dict) else {}
    return {
        "contract": item.get("contract"),
        "surface_ids": sorted(identifier_set(item.get("surface_ids"))),
        "causal_path": item.get("causal_path"),
        "stop_boundary": item.get("stop_boundary"),
        "probe": {
            "kind": probe.get("kind"),
            "description": probe.get("description"),
        },
        "coverage_points": [
            {
                "id": point.get("id"),
                "role": point.get("role"),
                "description": point.get("description"),
            }
            for point in item.get("coverage_points", [])
            if isinstance(point, dict)
        ],
    }


def catalog_signature(catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "target": catalog["target"],
        "gate_question": catalog["gate_question"],
        "current_contracts": sorted(catalog["current_contracts"]),
        "handoffs": {
            item_id: handoff_core(item)
            for item_id, item in sorted(catalog["handoffs"].items())
        },
        "target_surfaces": {
            item_id: surface_core(item)
            for item_id, item in sorted(catalog["target_surfaces"].items())
        },
        "artifact_coverage": catalog["artifact_coverage"],
        "catalog_check": catalog["catalog_check"],
        "review_dimensions": {
            item_id: dimension_core(item)
            for item_id, item in sorted(catalog["review_dimensions"].items())
        },
    }


def has_initial_coverage_catalog(brief: dict[str, Any]) -> bool:
    if any(field in brief for field in ("artifact_coverage", "catalog_check")):
        return True
    dimensions = brief.get("review_dimensions")
    return isinstance(dimensions, list) and any(
        isinstance(dimension, dict) and "coverage_points" in dimension
        for dimension in dimensions
    )


def validate_review_input(
    review_input: dict[str, Any],
    where: str,
    errors: list[str],
    *,
    require_initial_coverage: bool,
) -> dict[str, Any]:
    reject_fields(review_input, LEGACY_FIELDS, where, errors)
    require_identifier(review_input, "review_id", where, errors)
    condition_ids = unique_texts(
        review_input.get("condition_ids"),
        f"{where}.condition_ids",
        errors,
        allow_empty=True,
    )
    contracts = set(
        unique_texts(
            review_input.get("current_contracts"),
            f"{where}.current_contracts",
            errors,
            allow_empty=False,
        )
    )
    handoffs = unique_objects(
        review_input.get("handoffs"), f"{where}.handoffs", errors
    )
    artifacts: dict[str, dict[str, Any]] = {}
    if require_initial_coverage or "target_artifacts" in review_input:
        artifacts = unique_objects(
            review_input.get("target_artifacts"), f"{where}.target_artifacts", errors
        )
    if require_initial_coverage and not artifacts:
        errors.append(f"{where}.target_artifacts: 1件以上必要です")
    artifact_sources: set[str] = set()
    for artifact_id, artifact in artifacts.items():
        location = f"{where}.target_artifacts[{artifact_id}]"
        require_text(artifact, "source", location, errors)
        source = artifact.get("source")
        if text_value(source):
            if source in artifact_sources:
                errors.append(f"{location}.source: 対象成果が重複しています")
            artifact_sources.add(source)
    for handoff_id, handoff in handoffs.items():
        location = f"{where}.handoffs[{handoff_id}]"
        require_text(handoff, "gate", location, errors)
        require_text(handoff, "owner", location, errors)
        require_identifier(handoff, "contract", location, errors)
        if identifier_value(handoff.get("contract")) and handoff["contract"] not in contracts:
            errors.append(f"{location}.contract: current_contractsにない契約です")
    return {
        "review_id": review_input.get("review_id"),
        "condition_ids": condition_ids,
        "current_contracts": contracts,
        "handoffs": handoffs,
        "target_artifacts": artifacts,
    }


def validate_brief(
    brief: dict[str, Any],
    where: str,
    errors: list[str],
    review_input: dict[str, Any] | None = None,
    *,
    require_initial_coverage: bool,
) -> dict[str, Any]:
    reject_fields(brief, LEGACY_FIELDS, where, errors)
    require_identifier(brief, "review_id", where, errors)
    if brief.get("review_cycle") not in REVIEW_CYCLES:
        errors.append(f"{where}.review_cycle: initialまたはrereviewが必要です")
    require_text(brief, "target", where, errors)
    require_text(brief, "gate_question", where, errors)
    contracts = set(
        unique_texts(
            brief.get("current_contracts"),
            f"{where}.current_contracts",
            errors,
            allow_empty=False,
        )
    )

    handoffs = unique_objects(brief.get("handoffs"), f"{where}.handoffs", errors)
    for handoff_id, handoff in handoffs.items():
        location = f"{where}.handoffs[{handoff_id}]"
        require_text(handoff, "gate", location, errors)
        require_text(handoff, "owner", location, errors)
        require_identifier(handoff, "contract", location, errors)
        if identifier_value(handoff.get("contract")) and handoff["contract"] not in contracts:
            errors.append(f"{location}.contract: current_contractsにない契約です")

    surfaces = unique_objects(
        brief.get("target_surfaces"), f"{where}.target_surfaces", errors
    )
    condition_sources: list[str] = []
    covered_handoffs: set[str] = set()
    for surface_id, surface in surfaces.items():
        location = f"{where}.target_surfaces[{surface_id}]"
        if surface.get("kind") not in SURFACE_KINDS:
            errors.append(f"{location}.kind: 不明なsurface種別です")
        if surface.get("kind") == "condition":
            require_identifier(surface, "source", location, errors)
            if identifier_value(surface.get("source")):
                condition_sources.append(surface["source"])
        else:
            require_text(surface, "source", location, errors)
        require_identifier(surface, "contract", location, errors)
        if identifier_value(surface.get("contract")) and surface["contract"] not in contracts:
            errors.append(f"{location}.contract: current_contractsにない契約です")
        if surface.get("kind") == "handoff":
            require_identifier(surface, "handoff_id", location, errors)
            handoff = handoffs.get(surface.get("handoff_id"))
            if handoff is None:
                errors.append(f"{location}.handoff_id: handoffsにないIDです")
            elif handoff.get("contract") != surface.get("contract"):
                errors.append(f"{location}.contract: handoff契約と一致しません")
            else:
                covered_handoffs.add(surface["handoff_id"])
        elif "handoff_id" in surface:
            errors.append(f"{location}.handoff_id: handoff surface以外には指定できません")

    artifact_coverage: dict[str, dict[str, Any]] = {}
    raw_artifact_coverage = brief.get("artifact_coverage", [])
    if not isinstance(raw_artifact_coverage, list):
        errors.append(f"{where}.artifact_coverage: 配列が必要です")
        raw_artifact_coverage = []
    for index, item in enumerate(raw_artifact_coverage):
        location = f"{where}.artifact_coverage[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        require_identifier(item, "artifact_id", location, errors)
        artifact_id = item.get("artifact_id")
        if not identifier_value(artifact_id):
            continue
        if artifact_id in artifact_coverage:
            errors.append(f"{location}.artifact_id: 重複しています")
            continue
        artifact_coverage[artifact_id] = item
        classification = item.get("classification")
        if classification not in ARTIFACT_CLASSES:
            errors.append(f"{location}.classification: surfaceまたはexcludedが必要です")
        surface_ids = unique_texts(
            item.get("surface_ids", []),
            f"{location}.surface_ids",
            errors,
            allow_empty=True,
        )
        unknown_surfaces = set(surface_ids) - set(surfaces)
        if unknown_surfaces:
            errors.append(f"{location}.surface_ids: 不明なsurfaceです")
        if classification == "surface":
            if not surface_ids:
                errors.append(f"{location}.surface_ids: surface分類では1件以上必要です")
            if "reason" in item:
                errors.append(f"{location}.reason: surface分類には指定しません")
        elif classification == "excluded":
            if surface_ids:
                errors.append(f"{location}.surface_ids: excluded分類では空にしてください")
            require_text(item, "reason", location, errors)

    catalog_check = brief.get("catalog_check", {})
    if not isinstance(catalog_check, dict):
        errors.append(f"{where}.catalog_check: objectが必要です")
        catalog_check = {}
    if require_initial_coverage or "catalog_check" in brief:
        for field in ("upstream_trace", "downstream_trace", "independent_root_check"):
            require_text(catalog_check, field, f"{where}.catalog_check", errors)

    dimensions = unique_objects(
        brief.get("review_dimensions"), f"{where}.review_dimensions", errors
    )
    surface_coverage = {surface_id: 0 for surface_id in surfaces}
    contract_coverage = {contract: 0 for contract in contracts}
    coverage_point_ids: set[str] = set()
    for dimension_id, dimension in dimensions.items():
        location = f"{where}.review_dimensions[{dimension_id}]"
        require_identifier(dimension, "contract", location, errors)
        contract = dimension.get("contract")
        if identifier_value(contract):
            if contract not in contracts:
                errors.append(f"{location}.contract: current_contractsにない契約です")
            else:
                contract_coverage[contract] += 1
        surface_ids = unique_texts(
            dimension.get("surface_ids"),
            f"{location}.surface_ids",
            errors,
            allow_empty=False,
        )
        for surface_id in surface_ids:
            surface = surfaces.get(surface_id)
            if surface is None:
                errors.append(f"{location}.surface_ids: target_surfacesにないIDです: {surface_id}")
            else:
                surface_coverage[surface_id] += 1
                if surface.get("contract") != contract:
                    errors.append(
                        f"{location}.surface_ids: 異なる契約のsurfaceです: {surface_id}"
                    )
        require_text(dimension, "causal_path", location, errors)
        require_text(dimension, "stop_boundary", location, errors)
        probe = dimension.get("probe")
        if not isinstance(probe, dict):
            errors.append(f"{location}.probe: objectが必要です")
        else:
            if probe.get("kind") not in PROBE_KINDS:
                errors.append(f"{location}.probe.kind: 不明な確認方法です")
            require_text(probe, "description", f"{location}.probe", errors)
        coverage_points = dimension.get("coverage_points", [])
        if not isinstance(coverage_points, list):
            errors.append(f"{location}.coverage_points: 配列が必要です")
            coverage_points = []
        roles: set[str] = set()
        local_point_ids: set[str] = set()
        for point_index, point in enumerate(coverage_points):
            point_location = f"{location}.coverage_points[{point_index}]"
            if not isinstance(point, dict):
                errors.append(f"{point_location}: objectが必要です")
                continue
            require_identifier(point, "id", point_location, errors)
            point_id = point.get("id")
            if identifier_value(point_id):
                if point_id in local_point_ids or point_id in coverage_point_ids:
                    errors.append(f"{point_location}.id: review内で重複しています")
                local_point_ids.add(point_id)
                coverage_point_ids.add(point_id)
            role = point.get("role")
            if role not in COVERAGE_ROLES:
                errors.append(f"{point_location}.role: origin／mechanism／observationが必要です")
            else:
                roles.add(role)
            require_text(point, "description", point_location, errors)
        missing_roles = COVERAGE_ROLES - roles
        if (require_initial_coverage or "coverage_points" in dimension) and missing_roles:
            errors.append(
                f"{location}.coverage_points: 因果経路の役割が不足しています: {sorted(missing_roles)}"
            )

    if not dimensions:
        errors.append(f"{where}.review_dimensions: 1件以上必要です")
    for surface_id, count in sorted(surface_coverage.items()):
        if count < 1:
            errors.append(f"{where}.review_dimensions: 未被覆surfaceです: {surface_id}")
    for contract, count in sorted(contract_coverage.items()):
        if count < 1:
            errors.append(f"{where}.review_dimensions: 未被覆契約です: {contract}")
    for handoff_id in sorted(set(handoffs) - covered_handoffs):
        errors.append(f"{where}.target_surfaces: 未被覆handoffです: {handoff_id}")

    if review_input is not None:
        if brief.get("review_id") != review_input.get("review_id"):
            errors.append(f"{where}.review_id: Review Inputと一致しません")
        if contracts != review_input.get("current_contracts"):
            errors.append(f"{where}.current_contracts: Review Inputと一致しません")
        if {
            item_id: handoff_core(item) for item_id, item in handoffs.items()
        } != {
            item_id: handoff_core(item)
            for item_id, item in review_input.get("handoffs", {}).items()
        }:
            errors.append(f"{where}.handoffs: Review Inputと一致しません")
        if sorted(condition_sources) != sorted(review_input.get("condition_ids", [])):
            errors.append(f"{where}.target_surfaces: condition_idsと一致しません")
        if require_initial_coverage or "target_artifacts" in review_input:
            expected_artifacts = set(review_input.get("target_artifacts", {}))
            actual_artifacts = set(artifact_coverage)
            if actual_artifacts != expected_artifacts:
                errors.append(f"{where}.artifact_coverage: target_artifactsを過不足なく分類してください")

    return {
        "review_id": brief.get("review_id"),
        "review_cycle": brief.get("review_cycle"),
        "full_review_reason": brief.get("full_review_reason"),
        "target": brief.get("target"),
        "gate_question": brief.get("gate_question"),
        "current_contracts": contracts,
        "handoffs": handoffs,
        "target_surfaces": surfaces,
        "artifact_coverage": {
            artifact_id: {
                "classification": item.get("classification"),
                "surface_ids": sorted(identifier_set(item.get("surface_ids"))),
                "reason": item.get("reason"),
            }
            for artifact_id, item in sorted(artifact_coverage.items())
        },
        "catalog_check": {
            "upstream_trace": catalog_check.get("upstream_trace"),
            "downstream_trace": catalog_check.get("downstream_trace"),
            "independent_root_check": catalog_check.get("independent_root_check"),
        },
        "review_dimensions": dimensions,
    }


def validate_manifest_identity(
    manifest: dict[str, Any], catalog: dict[str, Any], where: str, errors: list[str]
) -> None:
    reject_fields(manifest, LEGACY_FIELDS, where, errors)
    require_identifier(manifest, "review_id", where, errors)
    if manifest.get("review_id") != catalog.get("review_id"):
        errors.append(f"{where}.review_id: Review Briefと一致しません")


def dimensions_for_surfaces(
    surface_ids: set[str], dimensions: dict[str, dict[str, Any]]
) -> set[str]:
    return {
        dimension_id
        for dimension_id, dimension in dimensions.items()
        if surface_ids & identifier_set(dimension.get("surface_ids"))
    }


def validate_review_meta(
    manifest: dict[str, Any], catalog: dict[str, Any], where: str, errors: list[str]
) -> tuple[str | None, list[dict[str, Any]], set[str]]:
    mode = manifest.get("review_mode")
    if mode not in REVIEW_MODES:
        errors.append(f"{where}.review_mode: fullまたはincrementalが必要です")
        mode = None
    raw_impacts = manifest.get("change_impacts")
    if not isinstance(raw_impacts, list):
        errors.append(f"{where}.change_impacts: 配列が必要です")
        raw_impacts = []
    impact_ids: set[str] = set()
    impacted: set[str] = set()
    unaffected_across_impacts: set[str] = set()
    surfaces_across_impacts: set[str] = set()
    for index, impact in enumerate(raw_impacts):
        location = f"{where}.change_impacts[{index}]"
        if not isinstance(impact, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        require_identifier(impact, "id", location, errors)
        impact_id = impact.get("id")
        if identifier_value(impact_id):
            if impact_id in impact_ids:
                errors.append(f"{location}.id: 重複しています")
            impact_ids.add(impact_id)
        cause = impact.get("cause")
        if cause not in IMPACT_CAUSES:
            errors.append(f"{location}.cause: 不明な変更種別です")
        require_text(impact, "reason", location, errors)
        surface_ids = unique_texts(
            impact.get("surface_ids"),
            f"{location}.surface_ids",
            errors,
            allow_empty=True,
        )
        dimension_ids = unique_texts(
            impact.get("dimension_ids"),
            f"{location}.dimension_ids",
            errors,
            allow_empty=True,
        )
        raw_unaffected = impact.get("unaffected_dimensions", [])
        if not isinstance(raw_unaffected, list):
            errors.append(f"{location}.unaffected_dimensions: 配列が必要です")
            raw_unaffected = []
        unaffected: dict[str, dict[str, Any]] = {}
        for unaffected_index, item in enumerate(raw_unaffected):
            unaffected_location = (
                f"{location}.unaffected_dimensions[{unaffected_index}]"
            )
            if not isinstance(item, dict):
                errors.append(f"{unaffected_location}: objectが必要です")
                continue
            require_identifier(item, "dimension_id", unaffected_location, errors)
            require_text(item, "unaffected_reason", unaffected_location, errors)
            dimension_id = item.get("dimension_id")
            if not identifier_value(dimension_id):
                continue
            if dimension_id in unaffected:
                errors.append(f"{unaffected_location}.dimension_id: 重複しています")
                continue
            unaffected[dimension_id] = item
        unknown_surfaces = set(surface_ids) - set(catalog["target_surfaces"])
        unknown_dimensions = set(dimension_ids) - set(catalog["review_dimensions"])
        unknown_unaffected = set(unaffected) - set(catalog["review_dimensions"])
        if unknown_surfaces:
            errors.append(f"{location}.surface_ids: 不明なsurfaceです")
        if unknown_dimensions:
            errors.append(f"{location}.dimension_ids: 不明な観点です")
        if unknown_unaffected:
            errors.append(f"{location}.unaffected_dimensions: 不明な観点です")
        known_surfaces = set(surface_ids) - unknown_surfaces
        known_dimensions = set(dimension_ids) - unknown_dimensions
        repeated_surfaces = known_surfaces & surfaces_across_impacts
        if repeated_surfaces:
            errors.append(f"{location}.surface_ids: 別impactと重複しています")
        surfaces_across_impacts.update(known_surfaces)
        repeated_dimensions = known_dimensions & impacted
        if repeated_dimensions:
            errors.append(f"{location}.dimension_ids: 別impactと重複しています")
        if known_dimensions & unaffected_across_impacts:
            errors.append(f"{location}.dimension_ids: 別impactでは非影響とされています")
        if set(unaffected) & impacted:
            errors.append(
                f"{location}.unaffected_dimensions: 別impactでは影響ありとされています"
            )
        if cause == "target-change":
            covering_dimensions = dimensions_for_surfaces(
                known_surfaces, catalog["review_dimensions"]
            )
            if not known_surfaces:
                errors.append(f"{location}.surface_ids: target-changeでは1件以上必要です")
            if not known_dimensions:
                errors.append(f"{location}.dimension_ids: 影響観点が1件以上必要です")
            if known_dimensions - covering_dimensions:
                errors.append(f"{location}.dimension_ids: 変更surfaceを覆わない観点です")
            expected_unaffected = covering_dimensions - known_dimensions
            if set(unaffected) != expected_unaffected:
                errors.append(
                    f"{location}.unaffected_dimensions: 非影響とする共有観点を過不足なく指定してください"
                )
        elif cause == "review-gap":
            if not known_dimensions:
                errors.append(f"{location}.dimension_ids: review-gapでは1件以上必要です")
            allowed_surfaces = {
                surface_id
                for dimension_id in known_dimensions
                for surface_id in identifier_set(
                    catalog["review_dimensions"][dimension_id].get("surface_ids")
                )
            }
            if known_surfaces - allowed_surfaces:
                errors.append(f"{location}.surface_ids: 指定観点に属さないsurfaceです")
            if raw_unaffected:
                errors.append(f"{location}.unaffected_dimensions: review-gapには不要です")
        impacted.update(known_dimensions)
        unaffected_across_impacts.update(unaffected)
    if mode == "full" and raw_impacts:
        errors.append(f"{where}.change_impacts: full reviewでは空配列が必要です")
    if mode == "incremental" and not raw_impacts:
        errors.append(f"{where}.change_impacts: incremental reviewでは1件以上必要です")
    return mode, raw_impacts, impacted


def scope_core(scope: dict[str, Any]) -> dict[str, Any]:
    return {
        dimension_id: {
            "classification": item.get("classification"),
        }
        for dimension_id, item in sorted(scope["dimension_scopes"].items())
    }


def scope_record(scope: dict[str, Any]) -> dict[str, Any]:
    return {
        dimension_id: {
            "classification": item.get("classification"),
            "evidence": item.get("evidence"),
            "reason": item.get("reason"),
        }
        for dimension_id, item in sorted(scope["dimension_scopes"].items())
    }


def validate_dimension_scopes(
    manifest: dict[str, Any], catalog: dict[str, Any], where: str, errors: list[str]
) -> dict[str, Any]:
    raw_scopes = manifest.get("dimension_scopes")
    if not isinstance(raw_scopes, list):
        errors.append(f"{where}.dimension_scopes: 配列が必要です")
        raw_scopes = []
    scopes: dict[str, dict[str, Any]] = {}
    applicable: set[str] = set()
    for index, item in enumerate(raw_scopes):
        location = f"{where}.dimension_scopes[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        require_identifier(item, "dimension_id", location, errors)
        dimension_id = item.get("dimension_id")
        if not identifier_value(dimension_id):
            continue
        if dimension_id in scopes:
            errors.append(f"{location}.dimension_id: 重複しています")
            continue
        scopes[dimension_id] = item
        dimension = catalog["review_dimensions"].get(dimension_id)
        if dimension is None:
            errors.append(f"{location}.dimension_id: Review Briefにない観点です")
            continue
        classification = item.get("classification")
        if classification not in SCOPE_CLASSES:
            errors.append(f"{location}.classification: 不明な分類です")
            continue
        require_text(item, "evidence", location, errors)
        if classification == "applicable":
            applicable.add(dimension_id)
        else:
            require_text(item, "reason", location, errors)
            surface_kinds = {
                catalog["target_surfaces"][surface_id].get("kind")
                for surface_id in identifier_set(dimension.get("surface_ids"))
                if surface_id in catalog["target_surfaces"]
            }
            if surface_kinds - {"changed-surface"}:
                errors.append(
                    f"{location}: condition／invariant／handoffを含む観点はnot-applicableにできません"
                )
    for dimension_id in catalog["review_dimensions"]:
        if dimension_id not in scopes:
            errors.append(f"{where}.dimension_scopes: 未分類の観点です: {dimension_id}")
    if not applicable:
        errors.append(f"{where}.dimension_scopes: applicable観点が1件以上必要です")
    return {"dimension_scopes": scopes, "applicable": applicable}


def validate_scope_stage_shape(
    manifest: dict[str, Any], where: str, errors: list[str]
) -> None:
    if manifest.get("state") != "scope-fixed":
        errors.append(f"{where}.state: scope-fixedが必要です")
    for field in ("dimension_results", "reviewers", "finding_candidates"):
        if field in manifest:
            errors.append(f"{where}.{field}: scope stageには置けません")


def validate_reviewers(
    manifest: dict[str, Any], where: str, errors: list[str]
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    reviewers = unique_objects(manifest.get("reviewers"), f"{where}.reviewers", errors)
    completed: set[str] = set()
    for reviewer_id, reviewer in reviewers.items():
        location = f"{where}.reviewers[{reviewer_id}]"
        status = reviewer.get("status")
        if status not in REVIEWER_STATES:
            errors.append(f"{location}.status: completedまたはreassignedが必要です")
        elif status == "completed":
            completed.add(reviewer_id)
        else:
            require_identifier(reviewer, "transferred_to", location, errors)
    for reviewer_id, reviewer in reviewers.items():
        if reviewer.get("status") == "reassigned" and reviewer.get("transferred_to") not in completed:
            errors.append(f"{where}.reviewers[{reviewer_id}]: completed担当への移譲が必要です")
    if not completed:
        errors.append(f"{where}.reviewers: completed担当が1件以上必要です")
    return reviewers, completed


def result_core(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "evidence_mode": result.get("evidence_mode"),
        "probe_result": result.get("probe_result"),
        "evidence": result.get("evidence"),
        "guarantee": result.get("guarantee"),
        "reviewer_id": result.get("reviewer_id"),
        "coverage_results": result.get("coverage_results"),
    }


def validate_results_base(
    manifest: dict[str, Any],
    catalog: dict[str, Any],
    scope: dict[str, Any],
    where: str,
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    reviewers, completed = validate_reviewers(manifest, where, errors)
    raw_results = manifest.get("dimension_results")
    if not isinstance(raw_results, list):
        errors.append(f"{where}.dimension_results: 配列が必要です")
        raw_results = []
    results: dict[str, dict[str, Any]] = {}
    for index, result in enumerate(raw_results):
        location = f"{where}.dimension_results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        require_identifier(result, "dimension_id", location, errors)
        dimension_id = result.get("dimension_id")
        if not identifier_value(dimension_id):
            continue
        if dimension_id in results:
            errors.append(f"{location}.dimension_id: 重複しています")
            continue
        results[dimension_id] = result
        if dimension_id not in scope["applicable"]:
            errors.append(f"{location}.dimension_id: applicableでない観点です")
        if result.get("status") not in RESULT_STATES:
            errors.append(f"{location}.status: 不明な状態です")
        if result.get("evidence_mode") not in EVIDENCE_MODES:
            errors.append(f"{location}.evidence_mode: 不明な証拠種別です")
        if result.get("result_source") not in RESULT_SOURCES:
            errors.append(f"{location}.result_source: freshまたはcarried-forwardが必要です")
        require_text(result, "probe_result", location, errors)
        require_text(result, "evidence", location, errors)
        require_text(result, "guarantee", location, errors)
        require_identifier(result, "reviewer_id", location, errors)
        if result.get("reviewer_id") not in completed:
            errors.append(f"{location}.reviewer_id: completed担当が必要です")
        dimension = catalog["review_dimensions"].get(dimension_id, {})
        expected_points = {
            point.get("id")
            for point in dimension.get("coverage_points", [])
            if isinstance(point, dict) and identifier_value(point.get("id"))
        }
        raw_coverage_results = result.get("coverage_results", [])
        if not isinstance(raw_coverage_results, list):
            errors.append(f"{location}.coverage_results: 配列が必要です")
            raw_coverage_results = []
        coverage_results: dict[str, dict[str, Any]] = {}
        for coverage_index, coverage in enumerate(raw_coverage_results):
            coverage_location = f"{location}.coverage_results[{coverage_index}]"
            if not isinstance(coverage, dict):
                errors.append(f"{coverage_location}: objectが必要です")
                continue
            require_identifier(coverage, "point_id", coverage_location, errors)
            point_id = coverage.get("point_id")
            if not identifier_value(point_id):
                continue
            if point_id in coverage_results:
                errors.append(f"{coverage_location}.point_id: 重複しています")
                continue
            coverage_results[point_id] = coverage
            if coverage.get("status") not in RESULT_STATES:
                errors.append(f"{coverage_location}.status: 不明な状態です")
            require_text(coverage, "evidence", coverage_location, errors)
        if (expected_points or "coverage_results" in result) and set(
            coverage_results
        ) != expected_points:
            errors.append(
                f"{location}.coverage_results: coverage pointを過不足なく確認してください"
            )
        point_statuses = {
            coverage.get("status") for coverage in coverage_results.values()
        }
        expected_status = (
            "violated"
            if "violated" in point_statuses
            else "unverified"
            if "unverified" in point_statuses
            else "satisfied"
        )
        if coverage_results and result.get("status") != expected_status:
            errors.append(
                f"{location}.status: coverage_resultsの集約結果は{expected_status}です"
            )
    for dimension_id in scope["applicable"]:
        if dimension_id not in results:
            errors.append(f"{where}.dimension_results: 未確認の観点です: {dimension_id}")
    return results, reviewers


def validate_discovery_shape(
    manifest: dict[str, Any],
    catalog: dict[str, Any],
    scope: dict[str, Any],
    mode: str | None,
    impacted: set[str],
    where: str,
    errors: list[str],
    *,
    previous_results: dict[str, dict[str, Any]] | None,
    verify_carry_forward: bool,
    candidate_stage: bool = False,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    expected_state = "candidate-sorted" if candidate_stage else "discovery-complete"
    if manifest.get("state") != expected_state:
        errors.append(f"{where}.state: {expected_state}が必要です")
    if not candidate_stage and "finding_candidates" in manifest:
        errors.append(f"{where}.finding_candidates: discovery stageには置けません")
    results, reviewers = validate_results_base(
        manifest, catalog, scope, where, errors
    )
    if mode == "full":
        for dimension_id, result in results.items():
            if result.get("result_source") != "fresh":
                errors.append(f"{where}.dimension_results[{dimension_id}]: full reviewではfreshが必要です")
            if "carry_forward_reason" in result:
                errors.append(f"{where}.dimension_results[{dimension_id}]: carry理由は不要です")
    elif mode == "incremental":
        for dimension_id, result in results.items():
            location = f"{where}.dimension_results[{dimension_id}]"
            if dimension_id in impacted:
                if result.get("result_source") != "fresh":
                    errors.append(f"{location}: 影響観点はfreshが必要です")
                if "carry_forward_reason" in result:
                    errors.append(f"{location}: carry理由は不要です")
            else:
                if result.get("result_source") != "carried-forward":
                    errors.append(f"{location}: 非影響観点はcarried-forwardが必要です")
                require_text(result, "carry_forward_reason", location, errors)
                if verify_carry_forward:
                    previous = (previous_results or {}).get(dimension_id)
                    if previous is None or result_core(result) != result_core(previous):
                        errors.append(f"{location}: 直前結果をそのまま引き継いでください")
    return results, reviewers


def validate_previous_discovery(
    previous: dict[str, Any],
    previous_catalog: dict[str, Any],
    errors: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    validate_manifest_identity(previous, previous_catalog, "previous discovery", errors)
    mode, _, impacted = validate_review_meta(
        previous, previous_catalog, "previous discovery", errors
    )
    scope = validate_dimension_scopes(
        previous, previous_catalog, "previous discovery", errors
    )
    results, _ = validate_discovery_shape(
        previous,
        previous_catalog,
        scope,
        mode,
        impacted,
        "previous discovery",
        errors,
        previous_results=None,
        verify_carry_forward=False,
    )
    return scope, results


def validate_review_relation(
    mode: str | None,
    catalog: dict[str, Any],
    scope: dict[str, Any],
    impacted: set[str],
    previous_brief_path: str | None,
    previous_discovery_path: str | None,
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]] | None, bool]:
    previous_brief = load_object(previous_brief_path, "previous Brief", errors)
    previous_discovery = load_object(
        previous_discovery_path, "previous discovery baseline", errors
    )
    cycle = catalog.get("review_cycle")
    if (previous_brief is None) != (previous_discovery is None):
        errors.append("previous Briefとprevious discovery baselineは一緒に指定してください")
        return None, False
    if cycle == "rereview" and previous_brief is None:
        errors.append("rereviewにはprevious Briefとprevious discoveryが必要です")
        return None, False
    if cycle == "initial" and previous_brief is not None:
        errors.append("initial reviewにはprevious baselineを指定できません")
    if cycle == "initial" and text_value(catalog.get("full_review_reason")):
        errors.append("initial reviewにはfull_review_reasonを指定しません")
    if mode == "incremental" and cycle != "rereview":
        errors.append("incremental reviewはreview_cycle: rereviewで行ってください")
    if cycle == "initial" and mode != "full":
        errors.append("initial reviewはfullで開始してください")
    if previous_brief is None or previous_discovery is None:
        return None, False

    previous_errors: list[str] = []
    previous_catalog = validate_brief(
        previous_brief,
        "previous brief",
        previous_errors,
        require_initial_coverage=has_initial_coverage_catalog(previous_brief),
    )
    previous_scope, previous_results = validate_previous_discovery(
        previous_discovery, previous_catalog, previous_errors
    )
    errors.extend(f"previous review: {error}" for error in previous_errors)
    catalog_changed = catalog_signature(catalog) != catalog_signature(previous_catalog)
    scope_changed = scope_core(scope) != scope_core(previous_scope)
    if cycle == "rereview" and catalog.get("review_id") != previous_catalog.get(
        "review_id"
    ):
        errors.append("rereviewではreview_idを変更できません")
    if mode == "incremental":
        if catalog_changed:
            errors.append("catalog変更時はfull reviewが必要です")
        if scope_changed:
            errors.append("scope分類変更時はfull reviewが必要です")
        elif scope_record(scope) != scope_record(previous_scope):
            errors.append("incremental reviewでは直前scope baselineをそのまま使ってください")
        non_applicable = impacted - scope["applicable"]
        if non_applicable:
            errors.append(f"not-applicable観点の影響はfull reviewが必要です: {sorted(non_applicable)}")
        if text_value(catalog.get("full_review_reason")):
            errors.append("incremental reviewにはfull_review_reasonを指定しません")
    elif mode == "full":
        if cycle == "rereview":
            if not text_value(catalog.get("full_review_reason")):
                errors.append("full rereviewにはfull_review_reasonが必要です")
            if not (catalog_changed or scope_changed):
                errors.append("catalog／scopeが同じ再レビューはincrementalで行ってください")
    return previous_results, True


def compare_fields(
    current: dict[str, Any],
    baseline: dict[str, Any],
    fields: tuple[str, ...],
    where: str,
    errors: list[str],
) -> None:
    for field in fields:
        if current.get(field) != baseline.get(field):
            errors.append(f"{where}.{field}: baselineから変更できません")


def validate_scope_baseline(
    baseline: dict[str, Any], catalog: dict[str, Any], errors: list[str]
) -> tuple[dict[str, Any], str | None, list[dict[str, Any]], set[str]]:
    validate_manifest_identity(baseline, catalog, "scope baseline", errors)
    mode, impacts, impacted = validate_review_meta(
        baseline, catalog, "scope baseline", errors
    )
    scope = validate_dimension_scopes(
        baseline, catalog, "scope baseline", errors
    )
    validate_scope_stage_shape(baseline, "scope baseline", errors)
    return scope, mode, impacts, impacted


def handoff_dimensions(catalog: dict[str, Any], handoff_id: str) -> set[str]:
    surface_ids = {
        surface_id
        for surface_id, surface in catalog["target_surfaces"].items()
        if surface.get("kind") == "handoff" and surface.get("handoff_id") == handoff_id
    }
    return dimensions_for_surfaces(surface_ids, catalog["review_dimensions"])


def validate_findings(
    manifest: dict[str, Any],
    catalog: dict[str, Any],
    results: dict[str, dict[str, Any]],
    mode: str | None,
    impacts: list[dict[str, Any]],
    errors: list[str],
) -> None:
    findings = unique_objects(
        manifest.get("finding_candidates"), "manifest.finding_candidates", errors
    )
    blocking_coverage: dict[str, int] = {}
    signatures: set[tuple[Any, ...]] = set()
    for finding_id, finding in findings.items():
        where = f"manifest.finding_candidates[{finding_id}]"
        routing = finding.get("routing")
        if routing not in ROUTINGS:
            errors.append(f"{where}.routing: 不明な振り分けです")
            continue
        dimension_ids = unique_texts(
            finding.get("dimension_ids"),
            f"{where}.dimension_ids",
            errors,
            allow_empty=False,
        )
        unknown = set(dimension_ids) - set(results)
        if unknown:
            errors.append(f"{where}.dimension_ids: 結果のない観点です")
        referenced = set(dimension_ids) - unknown
        require_text(finding, "reason", where, errors)
        conflicts = finding.get("conflicting_contracts", [])
        conflict_signature = tuple(sorted(identifier_set(conflicts)))
        signature = (
            routing,
            tuple(sorted(referenced)),
            finding.get("handoff_id"),
            conflict_signature,
        )
        if signature in signatures:
            errors.append(f"{where}: 同じ観点と振り分けの候補が重複しています")
        signatures.add(signature)
        statuses = {results[dimension_id].get("status") for dimension_id in referenced}
        if mode == "incremental":
            fresh_referenced = {
                dimension_id
                for dimension_id in referenced
                if results[dimension_id].get("result_source") == "fresh"
            }
            if fresh_referenced:
                origin = finding.get("origin")
                if origin not in {"prior-review-miss", "change-regression"}:
                    errors.append(
                        f"{where}.origin: prior-review-missまたはchange-regressionが必要です"
                    )
                require_text(finding, "origin_evidence", where, errors)
                expected_cause = {
                    "prior-review-miss": "review-gap",
                    "change-regression": "target-change",
                }.get(origin)
                matching_dimensions = {
                    dimension_id
                    for impact in impacts
                    if isinstance(impact, dict) and impact.get("cause") == expected_cause
                    for dimension_id in identifier_set(impact.get("dimension_ids"))
                }
                if expected_cause and not fresh_referenced.issubset(
                    matching_dimensions
                ):
                    errors.append(
                        f"{where}.origin: fresh観点のchange impactと整合しません"
                    )
            elif "origin" in finding or "origin_evidence" in finding:
                errors.append(f"{where}: 引き継いだfindingにはoriginを指定しません")
        elif "origin" in finding or "origin_evidence" in finding:
            errors.append(f"{where}: 初回full reviewにはoriginを指定しません")
        if routing == "fix-here":
            if statuses - {"violated"}:
                errors.append(f"{where}: fix-hereはviolated観点だけを参照してください")
            require_text(finding, "minimal_fix_boundary", where, errors)
            for dimension_id in referenced:
                blocking_coverage[dimension_id] = blocking_coverage.get(dimension_id, 0) + 1
        elif routing == "later-gate":
            if statuses - {"satisfied"}:
                errors.append(f"{where}: later-gateはsatisfied観点だけを参照してください")
            require_identifier(finding, "handoff_id", where, errors)
            handoff_id = finding.get("handoff_id")
            if handoff_id not in catalog["handoffs"]:
                errors.append(f"{where}.handoff_id: Review Briefにないhandoffです")
            elif not (referenced & handoff_dimensions(catalog, handoff_id)):
                errors.append(f"{where}.dimension_ids: handoff面を確認する観点が必要です")
        elif routing == "contract-decision":
            if statuses - {"violated"}:
                errors.append(f"{where}: contract-decisionはviolated観点だけを参照してください")
            conflict_ids = unique_texts(
                conflicts,
                f"{where}.conflicting_contracts",
                errors,
                allow_empty=False,
            )
            if len(conflict_ids) < 2:
                errors.append(f"{where}.conflicting_contracts: 2契約以上必要です")
            referenced_contracts = {
                catalog["review_dimensions"][dimension_id].get("contract")
                for dimension_id in referenced
                if dimension_id in catalog["review_dimensions"]
            }
            if not set(conflict_ids).issubset(referenced_contracts):
                errors.append(f"{where}: 衝突契約ごとの観点を参照してください")
            require_text(finding, "reachable_scenario", where, errors)
            for dimension_id in referenced:
                blocking_coverage[dimension_id] = blocking_coverage.get(dimension_id, 0) + 1
        else:
            if statuses - {"satisfied"}:
                errors.append(f"{where}: not-applicableはsatisfied観点だけを参照してください")

    for dimension_id, result in results.items():
        if result.get("status") == "unverified":
            errors.append(f"manifest: unverified観点があるためcandidate Gateへ進めません: {dimension_id}")
        if result.get("status") != "violated":
            continue
        count = blocking_coverage.get(dimension_id, 0)
        if count != 1:
            errors.append(f"manifest.finding_candidates: violated観点を一度だけ統合してください: {dimension_id}")


def main() -> int:
    args = parse_args()
    try:
        review_input = load_json(args.review_input)
        brief = load_json(args.brief)
        manifest = load_json(args.manifest)
    except (OSError, json.JSONDecodeError) as error:
        print(f"review-gate: JSONを読めません: {error}", file=sys.stderr)
        return 2
    if (
        not isinstance(review_input, dict)
        or not isinstance(brief, dict)
        or not isinstance(manifest, dict)
    ):
        print(
            "review-gate: Review Input、brief、manifestのrootはobjectが必要です",
            file=sys.stderr,
        )
        return 2

    errors: list[str] = []
    require_initial_coverage = (
        brief.get("review_cycle") == "initial"
        or has_initial_coverage_catalog(brief)
    )
    input_catalog = validate_review_input(
        review_input,
        "review input",
        errors,
        require_initial_coverage=require_initial_coverage,
    )
    catalog = validate_brief(
        brief,
        "brief",
        errors,
        input_catalog,
        require_initial_coverage=require_initial_coverage,
    )
    validate_manifest_identity(manifest, catalog, "manifest", errors)
    mode, impacts, impacted = validate_review_meta(
        manifest, catalog, "manifest", errors
    )
    scope = validate_dimension_scopes(manifest, catalog, "manifest", errors)

    if args.stage == "scope":
        if args.scope_baseline:
            errors.append("--scope-baseline: scope stageには不要です")
        if args.discovery_baseline:
            errors.append("--discovery-baseline: scope stageには不要です")
        validate_scope_stage_shape(manifest, "manifest", errors)
        validate_review_relation(
            mode,
            catalog,
            scope,
            impacted,
            args.previous_brief,
            args.previous_discovery_baseline,
            errors,
        )
    else:
        scope_baseline = load_object(args.scope_baseline, "scope baseline", errors)
        if scope_baseline is None:
            errors.append(f"--scope-baseline: {args.stage} stageでは必須です")
        else:
            baseline_errors: list[str] = []
            baseline_scope, baseline_mode, baseline_impacts, baseline_impacted = (
                validate_scope_baseline(scope_baseline, catalog, baseline_errors)
            )
            compare_fields(
                manifest,
                scope_baseline,
                ("review_id", "review_mode", "change_impacts", "dimension_scopes"),
                "manifest",
                errors,
            )
            if (
                mode != baseline_mode
                or impacts != baseline_impacts
                or impacted != baseline_impacted
                or scope_core(scope) != scope_core(baseline_scope)
            ):
                errors.append("manifest: scope baselineと一致しません")
            errors.extend(f"scope baseline: {error}" for error in baseline_errors)

        previous_results, _ = validate_review_relation(
            mode,
            catalog,
            scope,
            impacted,
            args.previous_brief,
            args.previous_discovery_baseline,
            errors,
        )
        results, reviewers = validate_discovery_shape(
            manifest,
            catalog,
            scope,
            mode,
            impacted,
            "manifest",
            errors,
            previous_results=previous_results,
            verify_carry_forward=True,
            candidate_stage=args.stage == "candidate",
        )

        if args.stage == "discovery":
            if args.discovery_baseline:
                errors.append("--discovery-baseline: discovery stageには不要です")
        else:
            discovery_baseline = load_object(
                args.discovery_baseline, "discovery baseline", errors
            )
            if discovery_baseline is None:
                errors.append("--discovery-baseline: candidate stageでは必須です")
            else:
                discovery_errors: list[str] = []
                validate_manifest_identity(
                    discovery_baseline,
                    catalog,
                    "discovery baseline",
                    discovery_errors,
                )
                discovery_mode, discovery_impacts, discovery_impacted = validate_review_meta(
                    discovery_baseline,
                    catalog,
                    "discovery baseline",
                    discovery_errors,
                )
                discovery_scope = validate_dimension_scopes(
                    discovery_baseline,
                    catalog,
                    "discovery baseline",
                    discovery_errors,
                )
                validate_discovery_shape(
                    discovery_baseline,
                    catalog,
                    discovery_scope,
                    discovery_mode,
                    discovery_impacted,
                    "discovery baseline",
                    discovery_errors,
                    previous_results=previous_results,
                    verify_carry_forward=True,
                )
                compare_fields(
                    manifest,
                    discovery_baseline,
                    (
                        "review_id",
                        "review_mode",
                        "change_impacts",
                        "dimension_scopes",
                        "dimension_results",
                        "reviewers",
                    ),
                    "manifest",
                    errors,
                )
                errors.extend(
                    f"discovery baseline: {error}" for error in discovery_errors
                )
            validate_findings(manifest, catalog, results, mode, impacts, errors)

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"review-gate: {args.stage} gate ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
