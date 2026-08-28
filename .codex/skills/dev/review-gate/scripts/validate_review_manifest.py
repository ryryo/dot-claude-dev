#!/usr/bin/env python3
"""Validate the structural exit conditions of review-gate.

This validator does not decide whether a contract or causal path is true. It
prevents a Gate review from advancing while required classifications and
evidence links are structurally missing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCOPE_CLASSES = {"applicable", "downstream", "not-applicable"}
SEED_KINDS = {"condition", "changed-surface", "invariant", "handoff"}
COVERAGE_OBLIGATIONS = {"must-applicable", "classify-only", "handoff-pair"}
UNIT_STATES = {"satisfied", "violated", "unverified"}
EVIDENCE_MODES = {"executed", "static", "existing"}
REVIEWER_STATES = {"completed", "reassigned"}
CHECKPOINT_REVIEWER_STATES = {"in-progress", "completed", "reassigned"}
ROUTINGS = {"fix-here", "later-gate", "contract-decision", "not-applicable"}
CaseOwner = tuple[Any, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="review-gateの適用範囲Gate／探索完了Gate／指摘採用Gateを検証する"
    )
    parser.add_argument(
        "--stage", choices=("scope", "discovery", "candidate"), required=True
    )
    parser.add_argument(
        "--review-input",
        required=True,
        help="レビュー開始前に正本から固定したcoverage baseline JSON",
    )
    parser.add_argument("--brief", required=True, help="main Codexが先に固定したReview Brief JSON")
    parser.add_argument(
        "--previous-brief",
        help="Review Brief revisionを上げる場合の直前revision JSON",
    )
    parser.add_argument(
        "--scope-baseline",
        help="scope stageで通過したmanifest。discovery/candidate stageでは必須",
    )
    parser.add_argument(
        "--previous-scope-baseline",
        help="探索中にscope Gateへ戻る場合の直前baseline。scope stageでだけ使用",
    )
    parser.add_argument(
        "--observation-checkpoint",
        help="applicableを再分類する直前の観測。scope再入場でtombstoneを追加する場合に必須",
    )
    parser.add_argument(
        "--discovery-baseline",
        help="discovery stageで通過したmanifest。candidate stageでは必須",
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="-",
        help="JSON manifest path。省略または-で標準入力",
    )
    return parser.parse_args()


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def text_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def identifier_value(value: Any) -> bool:
    return text_value(value) and value == value.strip()


def list_value(value: Any) -> bool:
    return isinstance(value, list)


def require_text(item: dict[str, Any], key: str, where: str, errors: list[str]) -> None:
    if not text_value(item.get(key)):
        errors.append(f"{where}.{key}: 空でない文字列が必要です")


def require_identifier(
    item: dict[str, Any], key: str, where: str, errors: list[str]
) -> None:
    value = item.get(key)
    if not text_value(value):
        errors.append(f"{where}.{key}: 空でない文字列が必要です")
    elif not identifier_value(value):
        errors.append(f"{where}.{key}: 前後空白は使用できません")


def require_unique_ids(items: Any, where: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not list_value(items):
        errors.append(f"{where}: 配列が必要です")
        return {}

    indexed: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(items):
        location = f"{where}[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        item_id = raw.get("id")
        if not text_value(item_id):
            errors.append(f"{location}.id: 空でない文字列が必要です")
            continue
        if not identifier_value(item_id):
            errors.append(f"{location}.id: 前後空白は使用できません")
            continue
        if item_id in indexed:
            errors.append(f"{location}.id: 重複しています: {item_id}")
            continue
        indexed[item_id] = raw
    return indexed


def validate_text_list(
    value: Any,
    where: str,
    errors: list[str],
    *,
    allow_empty: bool,
) -> list[str]:
    if not list_value(value) or (not allow_empty and not value):
        qualifier = "" if allow_empty else "空でない"
        errors.append(f"{where}: {qualifier}文字列の配列が必要です")
        return []
    if not all(text_value(item) for item in value):
        errors.append(f"{where}: 空でない文字列だけを指定してください")
        return []
    if not all(identifier_value(item) for item in value):
        errors.append(f"{where}: 前後空白は使用できません")
    if len(set(value)) != len(value):
        errors.append(f"{where}: 重複しています")
    return value


def validate_review_input(
    review_input: dict[str, Any], errors: list[str]
) -> tuple[
    str | None,
    set[str],
    set[str],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, CaseOwner],
    Any,
]:
    require_identifier(review_input, "review_id", "review_input", errors)
    condition_ids = validate_text_list(
        review_input.get("condition_ids"),
        "review_input.condition_ids",
        errors,
        allow_empty=True,
    )
    current_contracts = validate_text_list(
        review_input.get("current_contracts"),
        "review_input.current_contracts",
        errors,
        allow_empty=False,
    )
    review_id = review_input.get("review_id")
    catalog_errors: list[str] = []
    (
        _,
        handoffs,
        seeds,
        case_owners,
    ) = validate_brief(
        {
            "review_id": review_input.get("review_id"),
            "revision": 1,
            "target": "Review Input coverage baseline",
            "gate_question": "Review Input coverage baseline",
            "current_contracts": review_input.get("current_contracts"),
            "handoffs": review_input.get("handoffs"),
            "scope_seeds": review_input.get("scope_seeds"),
        },
        catalog_errors,
        expected_review_id=(
            review_id if identifier_value(review_id) else None
        ),
        expected_condition_ids=set(condition_ids),
        expected_contracts=set(current_contracts),
    )
    errors.extend(error.replace("brief.", "review_input.") for error in catalog_errors)
    if "previous_brief_digest" not in review_input:
        errors.append("review_input.previous_brief_digest: キーが必要です")
    return (
        review_id if identifier_value(review_id) else None,
        set(condition_ids),
        set(current_contracts),
        handoffs,
        seeds,
        case_owners,
        review_input.get("previous_brief_digest"),
    )


def validate_brief(
    brief: dict[str, Any],
    errors: list[str],
    *,
    expected_review_id: str | None = None,
    expected_condition_ids: set[str] | None = None,
    expected_contracts: set[str] | None = None,
) -> tuple[
    set[str],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, CaseOwner],
]:
    require_identifier(brief, "review_id", "brief", errors)
    revision = brief.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        errors.append("brief.revision: 正の整数が必要です")
    if expected_review_id is not None and brief.get("review_id") != expected_review_id:
        errors.append("brief.review_id: Review Inputと一致しません")
    require_text(brief, "target", "brief", errors)
    require_text(brief, "gate_question", "brief", errors)
    contracts = validate_text_list(
        brief.get("current_contracts"),
        "brief.current_contracts",
        errors,
        allow_empty=False,
    )
    current_contracts = set(contracts)
    if (
        expected_contracts is not None
        and (
            current_contracts != expected_contracts
            or not list_value(contracts)
            or len(contracts) != len(expected_contracts)
        )
    ):
        errors.append("brief.current_contracts: Review Inputの契約集合と一致しません")

    handoffs = require_unique_ids(brief.get("handoffs", []), "brief.handoffs", errors)
    for handoff_id, handoff in handoffs.items():
        where = f"brief.handoffs[{handoff_id}]"
        require_text(handoff, "gate", where, errors)
        require_text(handoff, "owner", where, errors)
        require_text(handoff, "contract", where, errors)
        if text_value(handoff.get("contract")) and handoff["contract"] not in current_contracts:
            errors.append(f"{where}.contract: current_contractsにないhandoff契約です")

    seeds = require_unique_ids(brief.get("scope_seeds"), "brief.scope_seeds", errors)
    covered_contracts: set[str] = set()
    covered_handoffs: set[str] = set()
    covered_conditions: dict[str, int] = {}
    review_case_owners: dict[str, CaseOwner] = {}
    for seed_id, seed in seeds.items():
        where = f"brief.scope_seeds[{seed_id}]"
        kind = seed.get("kind")
        if kind not in SEED_KINDS:
            errors.append(f"{where}.kind: {sorted(SEED_KINDS)} のいずれかが必要です")
        if kind == "condition":
            require_identifier(seed, "condition_id", where, errors)
            condition_id = seed.get("condition_id")
            if identifier_value(condition_id):
                covered_conditions[condition_id] = covered_conditions.get(condition_id, 0) + 1
                if (
                    expected_condition_ids is not None
                    and condition_id not in expected_condition_ids
                ):
                    errors.append(
                        f"{where}.condition_id: Review Inputにないcondition IDです"
                    )
        elif "condition_id" in seed:
            errors.append(f"{where}.condition_id: condition seed以外には指定できません")
        obligation = seed.get("coverage_obligation")
        if obligation not in COVERAGE_OBLIGATIONS:
            errors.append(
                f"{where}.coverage_obligation: {sorted(COVERAGE_OBLIGATIONS)} のいずれかが必要です"
            )
        elif seed.get("kind") in {"condition", "invariant"} and obligation != "must-applicable":
            errors.append(f"{where}.coverage_obligation: condition/invariantはmust-applicableです")
        elif seed.get("kind") == "handoff" and obligation != "handoff-pair":
            errors.append(f"{where}.coverage_obligation: handoffはhandoff-pairです")
        elif seed.get("kind") == "changed-surface" and obligation != "classify-only":
            errors.append(f"{where}.coverage_obligation: changed-surfaceはclassify-onlyです")
        case_ids = validate_text_list(
            seed.get("review_case_ids"),
            f"{where}.review_case_ids",
            errors,
            allow_empty=False,
        )
        require_text(seed, "source", where, errors)
        require_text(seed, "contract", where, errors)
        contract = seed.get("contract")
        if text_value(contract):
            if contract not in current_contracts:
                errors.append(f"{where}.contract: current_contractsにない契約です")
            else:
                covered_contracts.add(contract)
        if list_value(case_ids):
            for case_id in case_ids:
                if not identifier_value(case_id):
                    continue
                if case_id in review_case_owners:
                    errors.append(
                        f"{where}.review_case_ids: 全scope seedを通じて重複しています: {case_id}"
                    )
                    continue
                owned_handoff = (
                    handoffs.get(seed.get("handoff_id"))
                    if kind == "handoff"
                    else None
                )
                review_case_owners[case_id] = (
                    seed_id,
                    kind,
                    seed.get("source"),
                    contract if text_value(contract) else "",
                    seed.get("coverage_obligation"),
                    seed.get("condition_id") if kind == "condition" else None,
                    seed.get("handoff_id") if kind == "handoff" else None,
                    owned_handoff.get("gate") if owned_handoff is not None else None,
                    owned_handoff.get("owner") if owned_handoff is not None else None,
                    owned_handoff.get("contract")
                    if owned_handoff is not None
                    else None,
                )
        if seed.get("kind") == "handoff":
            require_identifier(seed, "handoff_id", where, errors)
            handoff = handoffs.get(seed.get("handoff_id"))
            if handoff is None:
                errors.append(f"{where}.handoff_id: brief.handoffsにないhandoffです")
            elif handoff.get("contract") != contract:
                errors.append(f"{where}.contract: handoff契約と一致しません")
            else:
                covered_handoffs.add(seed["handoff_id"])
        elif "handoff_id" in seed:
            errors.append(f"{where}.handoff_id: handoff seed以外には指定できません")

    missing_contract_seeds = current_contracts - covered_contracts
    if missing_contract_seeds:
        errors.append(f"brief.scope_seeds: seedのない契約があります: {sorted(missing_contract_seeds)}")
    missing_handoff_seeds = set(handoffs) - covered_handoffs
    if missing_handoff_seeds:
        errors.append(f"brief.scope_seeds: seedのないhandoffがあります: {sorted(missing_handoff_seeds)}")
    if expected_condition_ids is not None:
        for condition_id in sorted(expected_condition_ids | set(covered_conditions)):
            count = covered_conditions.get(condition_id, 0)
            if condition_id in expected_condition_ids and count != 1:
                errors.append(
                    "brief.scope_seeds: Review Inputのcondition IDはcondition seedで"
                    f"一度だけ被覆してください: {condition_id} ({count}件)"
                )
    return current_contracts, handoffs, seeds, review_case_owners


def canonical_json_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def validate_coverage_baseline_match(
    input_handoffs: dict[str, dict[str, Any]],
    input_seeds: dict[str, dict[str, Any]],
    brief_handoffs: dict[str, dict[str, Any]],
    brief_seeds: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if set(input_handoffs) != set(brief_handoffs):
        errors.append(
            "brief.handoffs: Review Inputのhandoff ID集合と一致しません"
        )
    for handoff_id in sorted(set(input_handoffs) & set(brief_handoffs)):
        for field in ("gate", "owner", "contract"):
            if input_handoffs[handoff_id].get(field) != brief_handoffs[
                handoff_id
            ].get(field):
                errors.append(
                    f"brief.handoffs[{handoff_id}].{field}: Review Inputと一致しません"
                )

    if set(input_seeds) != set(brief_seeds):
        errors.append(
            "brief.scope_seeds: Review Inputのseed ID集合と一致しません"
        )
    for seed_id in sorted(set(input_seeds) & set(brief_seeds)):
        input_seed = input_seeds[seed_id]
        brief_seed = brief_seeds[seed_id]
        for field in (
            "kind",
            "source",
            "contract",
            "coverage_obligation",
            "condition_id",
            "handoff_id",
        ):
            if input_seed.get(field) != brief_seed.get(field):
                errors.append(
                    f"brief.scope_seeds[{seed_id}].{field}: Review Inputと一致しません"
                )
        input_cases = input_seed.get("review_case_ids")
        brief_cases = brief_seed.get("review_case_ids")
        if (
            not list_value(input_cases)
            or not list_value(brief_cases)
            or len(input_cases) != len(brief_cases)
            or set(input_cases) != set(brief_cases)
        ):
            errors.append(
                f"brief.scope_seeds[{seed_id}].review_case_ids: Review Inputのcase集合と一致しません"
            )


def validate_brief_revision_shape(
    brief: dict[str, Any], where: str, errors: list[str]
) -> None:
    revision = brief.get("revision")
    if revision == 1 and not isinstance(revision, bool):
        if (
            "review_case_migrations" not in brief
            or brief.get("review_case_migrations") != []
        ):
            errors.append(
                f"{where}.review_case_migrations: revision 1ではキーと空配列[]が必要です"
            )
    elif (
        isinstance(revision, int)
        and not isinstance(revision, bool)
        and revision > 1
        and not list_value(brief.get("review_case_migrations"))
    ):
        errors.append(
            f"{where}.review_case_migrations: revision 2以降では配列が必要です"
        )


def validate_review_case_migrations(
    brief: dict[str, Any],
    previous_case_owners: dict[str, CaseOwner],
    current_case_owners: dict[str, CaseOwner],
    errors: list[str],
) -> None:
    migrations = brief.get("review_case_migrations")
    if not list_value(migrations):
        errors.append("brief.review_case_migrations: 配列が必要です")
        return

    previous_counts = {case_id: 0 for case_id in previous_case_owners}
    current_counts = {case_id: 0 for case_id in current_case_owners}
    for index, raw in enumerate(migrations):
        where = f"brief.review_case_migrations[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{where}: objectが必要です")
            continue
        previous_ids = validate_text_list(
            raw.get("previous_review_case_ids"),
            f"{where}.previous_review_case_ids",
            errors,
            allow_empty=True,
        )
        current_ids = validate_text_list(
            raw.get("current_review_case_ids"),
            f"{where}.current_review_case_ids",
            errors,
            allow_empty=True,
        )
        if not previous_ids and not current_ids:
            errors.append(f"{where}: 旧caseと現caseの両方を空にはできません")

        unknown_previous = set(previous_ids) - set(previous_case_owners)
        unknown_current = set(current_ids) - set(current_case_owners)
        if unknown_previous:
            errors.append(
                f"{where}.previous_review_case_ids: 直前Briefにないcaseです: {sorted(unknown_previous)}"
            )
        if unknown_current:
            errors.append(
                f"{where}.current_review_case_ids: 現Briefにないcaseです: {sorted(unknown_current)}"
            )
        for case_id in previous_ids:
            if case_id in previous_counts:
                previous_counts[case_id] += 1
        for case_id in current_ids:
            if case_id in current_counts:
                current_counts[case_id] += 1

        unchanged = (
            set(previous_ids) == set(current_ids)
            and len(previous_ids) == len(current_ids)
            and all(
                previous_case_owners.get(case_id) == current_case_owners.get(case_id)
                for case_id in set(previous_ids)
            )
        )
        if not unchanged:
            require_text(raw, "reason", where, errors)

    for case_id, count in sorted(previous_counts.items()):
        if count != 1:
            errors.append(
                "brief.review_case_migrations: 直前Briefのcaseを一度ずつ移行してください: "
                f"{case_id} ({count}件)"
            )
    for case_id, count in sorted(current_counts.items()):
        if count != 1:
            errors.append(
                "brief.review_case_migrations: 現Briefのcaseを一度ずつ移行してください: "
                f"{case_id} ({count}件)"
            )


def validate_scope(
    manifest: dict[str, Any],
    brief: dict[str, Any],
    current_contracts: set[str],
    handoffs: dict[str, dict[str, Any]],
    seeds: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], set[str], set[str]]:
    if manifest.get("review_id") != brief.get("review_id"):
        errors.append("manifest.review_id: Review Briefと一致しません")
    manifest_revision = manifest.get("brief_revision")
    if (
        isinstance(manifest_revision, bool)
        or not isinstance(manifest_revision, int)
        or manifest_revision < 1
    ):
        errors.append("manifest.brief_revision: 正の整数が必要です")
    elif manifest_revision != brief.get("revision"):
        errors.append("manifest.brief_revision: Review Briefと一致しません")
    require_text(manifest, "target", "manifest", errors)
    require_text(manifest, "gate_question", "manifest", errors)
    if manifest.get("target") != brief.get("target"):
        errors.append("manifest.target: Review Briefと一致しません")
    if manifest.get("gate_question") != brief.get("gate_question"):
        errors.append("manifest.gate_question: Review Briefと一致しません")
    if manifest.get("scope_gate") != "passed":
        errors.append("manifest.scope_gate: passedである必要があります")

    contracts = manifest.get("current_contracts")
    if not list_value(contracts) or set(contracts) != current_contracts or len(contracts) != len(current_contracts):
        errors.append("manifest.current_contracts: Review Briefの契約集合と一致しません")

    scope_items = require_unique_ids(manifest.get("scope_candidates"), "scope_candidates", errors)
    applicable: set[str] = set()
    downstream: set[str] = set()
    covered_seeds: set[str] = set()
    candidates_by_seed: dict[str, list[dict[str, Any]]] = {}
    scope_signatures: dict[str, str] = {}
    scope_case_counts: dict[str, int] = {}

    if not scope_items:
        errors.append("scope_candidates: 1件以上必要です")

    for item_id, item in scope_items.items():
        where = f"scope_candidates[{item_id}]"
        classification = item.get("classification")
        if classification not in SCOPE_CLASSES:
            errors.append(f"{where}.classification: {sorted(SCOPE_CLASSES)} のいずれかが必要です")
            continue

        require_identifier(item, "seed_id", where, errors)
        seed = seeds.get(item.get("seed_id"))
        if seed is None:
            errors.append(f"{where}.seed_id: Review Briefにないseedです")
        else:
            covered_seeds.add(item["seed_id"])
            candidates_by_seed.setdefault(item["seed_id"], []).append(item)
        require_text(item, "boundary", where, errors)
        if classification == "applicable":
            applicable.add(item_id)
            require_text(item, "contract", where, errors)
            require_text(item, "reachable_path", where, errors)
            require_identifier(item, "path_id", where, errors)
            case_ids = validate_text_list(
                item.get("review_case_ids"),
                f"{where}.review_case_ids",
                errors,
                allow_empty=False,
            )
            for case_id in case_ids:
                if identifier_value(case_id):
                    scope_case_counts[case_id] = scope_case_counts.get(case_id, 0) + 1
            if text_value(item.get("contract")) and item["contract"] not in current_contracts:
                errors.append(f"{where}.contract: current_contractsにない契約を適用できません")
            if seed is not None and item.get("contract") != seed.get("contract"):
                errors.append(f"{where}.contract: seedの契約と一致しません")
            if seed is not None and list_value(case_ids):
                unknown_cases = set(case_ids) - set(seed.get("review_case_ids", []))
                if unknown_cases:
                    errors.append(
                        f"{where}.review_case_ids: Review Briefにない確認caseです: {sorted(unknown_cases)}"
                    )
        elif classification == "downstream":
            downstream.add(item_id)
            require_identifier(item, "handoff_id", where, errors)
            require_text(item, "gate", where, errors)
            require_text(item, "owner", where, errors)
            require_text(item, "handoff_contract", where, errors)
            require_text(item, "reachable_path", where, errors)
            require_identifier(item, "path_id", where, errors)
            require_identifier(
                item, "handoff_review_scope_candidate_id", where, errors
            )
            if text_value(item.get("handoff_contract")) and item["handoff_contract"] not in current_contracts:
                errors.append(f"{where}.handoff_contract: current_contractsにない契約を後工程へ送れません")
            handoff = handoffs.get(item.get("handoff_id"))
            if handoff is None:
                errors.append(f"{where}.handoff_id: Review Briefにないhandoffです")
            elif (
                item.get("gate") != handoff.get("gate")
                or item.get("owner") != handoff.get("owner")
                or item.get("handoff_contract") != handoff.get("contract")
            ):
                errors.append(f"{where}: Review Briefのhandoff内容と一致しません")
            if seed is not None and (
                seed.get("kind") != "handoff"
                or seed.get("handoff_id") != item.get("handoff_id")
                or seed.get("contract") != item.get("handoff_contract")
            ):
                errors.append(f"{where}: handoff seedと一致しません")
        else:
            require_text(item, "reason", where, errors)

        if classification == "applicable":
            signature_core = (
                classification,
                item.get("seed_id"),
                item.get("contract"),
                item.get("path_id"),
            )
        elif classification == "downstream":
            signature_core = (
                classification,
                item.get("seed_id"),
                item.get("handoff_id"),
                item.get("path_id"),
            )
        else:
            signature_core = (classification, item.get("seed_id"))
        signature = json.dumps(signature_core, ensure_ascii=False, sort_keys=True)
        previous_id = scope_signatures.get(signature)
        if previous_id is not None:
            errors.append(
                f"{where}: 同じseed・分類・経路の重複scope候補です: {previous_id}"
            )
        else:
            scope_signatures[signature] = item_id

    if not applicable:
        errors.append("scope_candidates: applicableが1件以上必要です")
    missing_seeds = set(seeds) - covered_seeds
    if missing_seeds:
        errors.append(f"scope_candidates: 候補へ対応していないseedがあります: {sorted(missing_seeds)}")

    for seed_id, seed in seeds.items():
        seed_items = candidates_by_seed.get(seed_id, [])
        seed_classes = {item.get("classification") for item in seed_items}
        where = f"scope_candidates(seed={seed_id})"
        obligation = seed.get("coverage_obligation")
        if obligation == "must-applicable" and "applicable" not in seed_classes:
            errors.append(f"{where}: must-applicable seedにはapplicable候補が必要です")
        if obligation == "handoff-pair":
            if "applicable" not in seed_classes or "downstream" not in seed_classes:
                errors.append(
                    f"{where}: handoff-pair seedごとにapplicableとdownstreamの両候補が必要です"
                )
        applicable_items = [
            item
            for item in seed_items
            if item.get("classification") == "applicable"
        ]
        if applicable_items:
            case_counts: dict[str, int] = {
                case_id: 0 for case_id in seed.get("review_case_ids", [])
            }
            for item in applicable_items:
                for case_id in item.get("review_case_ids", []):
                    if case_id in case_counts:
                        case_counts[case_id] += 1
            for case_id, count in case_counts.items():
                if count != 1:
                    errors.append(
                        f"{where}: Review Briefの確認caseはapplicable候補へ一度だけ割り当ててください: {case_id} ({count}件)"
                    )

    for case_id, count in sorted(scope_case_counts.items()):
        if count > 1:
            errors.append(
                "scope_candidates: 同じ確認caseを複数のapplicable候補へ割り当てられません: "
                f"{case_id} ({count}件)"
            )

    for item_id in downstream:
        item = scope_items[item_id]
        producer_id = item.get("handoff_review_scope_candidate_id")
        producer = scope_items.get(producer_id)
        where = f"scope_candidates[{item_id}]"
        if producer_id not in applicable or producer is None:
            errors.append(f"{where}.handoff_review_scope_candidate_id: applicable候補を参照してください")
            continue
        if (
            producer.get("contract") != item.get("handoff_contract")
            or producer.get("seed_id") != item.get("seed_id")
            or producer.get("path_id") != item.get("path_id")
        ):
            errors.append(f"{where}: handoff面を確認するapplicable候補と一致しません")

    for seed_id, seed in seeds.items():
        if seed.get("kind") != "handoff":
            continue
        matching_downstream = [
            item
            for item in candidates_by_seed.get(seed_id, [])
            if item.get("classification") == "downstream"
            and item.get("handoff_id") == seed.get("handoff_id")
        ]
        if not matching_downstream:
            errors.append(
                f"scope_candidates: handoff seedにdownstream候補がありません: {seed_id}"
            )
    return scope_items, applicable, downstream


def scope_core(item: dict[str, Any]) -> dict[str, Any]:
    keys = {
        "classification",
        "seed_id",
        "path_id",
        "contract",
        "reachable_path",
        "boundary",
        "reason",
        "handoff_id",
        "gate",
        "owner",
        "handoff_contract",
        "handoff_review_scope_candidate_id",
        "review_case_ids",
    }
    return {key: item.get(key) for key in keys if key in item}


def validate_tombstones(
    manifest: dict[str, Any],
    scope_items: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    tombstones = require_unique_ids(
        manifest.get("scope_tombstones", []), "scope_tombstones", errors
    )
    origin_signatures: dict[tuple[Any, Any], str] = {}
    for tombstone_id, tombstone in tombstones.items():
        where = f"scope_tombstones[{tombstone_id}]"
        require_identifier(tombstone, "scope_candidate_id", where, errors)
        require_identifier(tombstone, "origin_review_unit_id", where, errors)
        require_identifier(tombstone, "origin_review_case_id", where, errors)
        require_identifier(tombstone, "reviewer_id", where, errors)
        if tombstone.get("previous_classification") != "applicable":
            errors.append(f"{where}.previous_classification: applicableが必要です")
        scope_id = tombstone.get("scope_candidate_id")
        current = scope_items.get(scope_id)
        if current is None or current.get("classification") == "applicable":
            errors.append(f"{where}.scope_candidate_id: 適用外へ再分類した候補を指定してください")
        if tombstone.get("status") not in UNIT_STATES:
            errors.append(f"{where}.status: {sorted(UNIT_STATES)} のいずれかが必要です")
        if tombstone.get("evidence_mode") not in EVIDENCE_MODES:
            errors.append(f"{where}.evidence_mode: {sorted(EVIDENCE_MODES)} のいずれかが必要です")
        require_text(tombstone, "evidence", where, errors)
        require_text(tombstone, "guarantee", where, errors)
        signature = (
            tombstone.get("scope_candidate_id"),
            tombstone.get("origin_review_case_id"),
        )
        previous_id = origin_signatures.get(signature)
        if previous_id is not None:
            errors.append(f"{where}: 同じ観測由来のtombstoneが重複しています: {previous_id}")
        else:
            origin_signatures[signature] = tombstone_id
    return tombstones


def validate_scope_transition(
    baseline_manifest: dict[str, Any],
    baseline_items: dict[str, dict[str, Any]],
    final_manifest: dict[str, Any],
    final_items: dict[str, dict[str, Any]],
    *,
    allow_scope_changes: bool,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    baseline_tombstones = validate_tombstones(
        baseline_manifest, baseline_items, errors
    )
    final_tombstones = validate_tombstones(final_manifest, final_items, errors)

    for tombstone_id, baseline_tombstone in baseline_tombstones.items():
        final_tombstone = final_tombstones.get(tombstone_id)
        if final_tombstone is None:
            errors.append(f"scope_tombstones[{tombstone_id}]: baselineから削除できません")
        elif final_tombstone != baseline_tombstone:
            errors.append(
                f"scope_tombstones[{tombstone_id}]: status・証拠・由来を変更できません"
            )

    if not allow_scope_changes:
        if set(final_items) != set(baseline_items):
            added = set(final_items) - set(baseline_items)
            removed = set(baseline_items) - set(final_items)
            if added:
                errors.append(
                    f"scope_candidates: scope Gate未通過の候補を追加できません: {sorted(added)}"
                )
            if removed:
                errors.append(
                    f"scope_candidates: scope baselineの候補を削除できません: {sorted(removed)}"
                )
        for item_id in set(final_items) & set(baseline_items):
            if final_items[item_id] != baseline_items[item_id]:
                errors.append(
                    f"scope_candidates[{item_id}]: scope Gate後に候補を変更できません"
                )
        new_tombstones = set(final_tombstones) - set(baseline_tombstones)
        if new_tombstones:
            errors.append(
                f"scope_tombstones: scope Gate未通過の履歴を追加できません: {sorted(new_tombstones)}"
            )
        return final_tombstones

    tombstones_by_scope: dict[str, list[dict[str, Any]]] = {}
    for tombstone_id in set(final_tombstones) - set(baseline_tombstones):
        tombstone = final_tombstones[tombstone_id]
        scope_id = tombstone.get("scope_candidate_id")
        baseline = baseline_items.get(scope_id)
        if baseline is None or baseline.get("classification") != "applicable":
            errors.append(
                f"scope_tombstones[{tombstone_id}].scope_candidate_id: 直前baselineのapplicable候補を指定してください"
            )
        if text_value(scope_id):
            tombstones_by_scope.setdefault(scope_id, []).append(tombstone)

    for item_id, baseline in baseline_items.items():
        final = final_items.get(item_id)
        where = f"scope_candidates[{item_id}]"
        if final is None:
            errors.append(f"{where}: scope baselineの候補を削除できません")
            continue
        if final == baseline:
            continue
        if scope_core(final) == scope_core(baseline):
            errors.append(f"{where}: 再分類metadataだけを追加できません")
            continue
        if final.get("classification") == baseline.get("classification"):
            errors.append(f"{where}: 同じIDの契約・経路・境界を黙って変更できません")
            continue
        if final.get("previous_classification") != baseline.get("classification"):
            errors.append(f"{where}.previous_classification: baselineの分類が必要です")
        require_text(final, "reclassification_reason", where, errors)
        require_text(final, "reclassification_evidence", where, errors)
        if baseline.get("classification") == "applicable" and not tombstones_by_scope.get(item_id):
            errors.append(f"{where}: applicableから外す場合は新しいscope_tombstoneが必要です")

    for item_id, final in final_items.items():
        if item_id in baseline_items:
            continue
        where = f"scope_candidates[{item_id}]"
        if final.get("added_during_discovery") is not True:
            errors.append(f"{where}.added_during_discovery: trueが必要です")
        require_text(final, "addition_reason", where, errors)
    return final_tombstones


def validate_scope_stage_shape(
    manifest: dict[str, Any], *, is_rescope: bool, errors: list[str]
) -> None:
    forbidden = ("discovery_gate", "candidate_gate", "review_units", "reviewers", "finding_candidates")
    for field in forbidden:
        if field in manifest:
            errors.append(f"manifest.{field}: scope stageには置けません")
    tombstones = manifest.get("scope_tombstones", [])
    if not is_rescope and tombstones not in (None, []):
        errors.append("manifest.scope_tombstones: 初回scope stageには置けません")
    transition_fields = {
        "previous_classification",
        "reclassification_reason",
        "reclassification_evidence",
        "added_during_discovery",
        "addition_reason",
    }
    if not is_rescope:
        for index, item in enumerate(manifest.get("scope_candidates", [])):
            if not isinstance(item, dict):
                continue
            present = transition_fields & set(item)
            if present:
                errors.append(
                    f"scope_candidates[{index}]: 初回scope stageに再探索metadataを置けません: {sorted(present)}"
                )


def validate_observation_checkpoint(
    checkpoint: dict[str, Any],
    scope_items: dict[str, dict[str, Any]],
    applicable: set[str],
    required_scope_ids: set[str],
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if checkpoint.get("state") != "discovery-in-progress":
        errors.append("observation checkpoint.state: discovery-in-progressである必要があります")
    for field in ("discovery_gate", "candidate_gate", "finding_candidates"):
        if field in checkpoint:
            errors.append(f"observation checkpoint.{field}: 観測checkpointには置けません")

    reviewers = require_unique_ids(
        checkpoint.get("reviewers"), "observation checkpoint.reviewers", errors
    )
    for reviewer_id, reviewer in reviewers.items():
        where = f"observation checkpoint.reviewers[{reviewer_id}]"
        if reviewer.get("status") not in CHECKPOINT_REVIEWER_STATES:
            errors.append(
                f"{where}.status: {sorted(CHECKPOINT_REVIEWER_STATES)} のいずれかが必要です"
            )

    units = require_unique_ids(
        checkpoint.get("review_units"), "observation checkpoint.review_units", errors
    )
    unit_signatures: dict[tuple[Any, ...], str] = {}
    covered_cases: dict[tuple[str, str], int] = {}
    covered_review_cases: dict[str, int] = {}
    for unit_id, unit in units.items():
        where = f"observation checkpoint.review_units[{unit_id}]"
        refs = unit.get("scope_candidate_ids")
        if not list_value(refs) or len(refs) != 1 or not all(text_value(value) for value in refs):
            errors.append(f"{where}.scope_candidate_ids: 一つのapplicable候補だけを指定してください")
        elif refs[0] not in applicable:
            errors.append(f"{where}.scope_candidate_ids: applicable候補を指定してください")
        require_text(unit, "contract", where, errors)
        require_text(unit, "reachable_path", where, errors)
        require_identifier(unit, "path_id", where, errors)
        require_identifier(unit, "review_case_id", where, errors)
        require_text(unit, "boundary", where, errors)
        require_text(unit, "evidence", where, errors)
        require_text(unit, "guarantee", where, errors)
        require_identifier(unit, "reviewer_id", where, errors)
        if unit.get("status") not in UNIT_STATES:
            errors.append(f"{where}.status: {sorted(UNIT_STATES)} のいずれかが必要です")
        if unit.get("evidence_mode") not in EVIDENCE_MODES:
            errors.append(f"{where}.evidence_mode: {sorted(EVIDENCE_MODES)} のいずれかが必要です")
        if unit.get("reviewer_id") not in reviewers:
            errors.append(f"{where}.reviewer_id: checkpoint内のreviewerを指定してください")
        if list_value(refs) and len(refs) == 1 and refs[0] in scope_items:
            scope_item = scope_items[refs[0]]
            if unit.get("contract") != scope_item.get("contract"):
                errors.append(f"{where}.contract: scope候補の契約と一致しません")
            if unit.get("path_id") != scope_item.get("path_id"):
                errors.append(f"{where}.path_id: scope候補のpath_idと一致しません")
            if unit.get("review_case_id") not in scope_item.get("review_case_ids", []):
                errors.append(f"{where}.review_case_id: scope Gateにない確認caseです")
            elif text_value(unit.get("review_case_id")):
                case_key = (refs[0], unit["review_case_id"])
                covered_cases[case_key] = covered_cases.get(case_key, 0) + 1
                covered_review_cases[unit["review_case_id"]] = (
                    covered_review_cases.get(unit["review_case_id"], 0) + 1
                )
        signature = (
            refs[0] if list_value(refs) and len(refs) == 1 else None,
            unit.get("review_case_id"),
        )
        previous_id = unit_signatures.get(signature)
        if previous_id is not None:
            errors.append(f"{where}: 同じscope確認caseが重複しています: {previous_id}")
        else:
            unit_signatures[signature] = unit_id
    for case_id, count in sorted(covered_review_cases.items()):
        if count > 1:
            errors.append(
                "observation checkpoint.review_units: 同じ確認caseを複数の確認単位へ割り当てられません: "
                f"{case_id} ({count}件)"
            )
    for scope_id in sorted(required_scope_ids):
        scope_item = scope_items.get(scope_id)
        if scope_item is None:
            continue
        for case_id in scope_item.get("review_case_ids", []):
            count = covered_cases.get((scope_id, case_id), 0)
            if count != 1:
                errors.append(
                    "observation checkpoint.review_units: 再分類するscopeの全確認caseを一度ずつ保持してください: "
                    f"{scope_id}/{case_id} ({count}件)"
                )
    return units, reviewers


def validate_tombstone_origins(
    tombstones: dict[str, dict[str, Any]],
    checkpoint_units: dict[str, dict[str, Any]],
    checkpoint_reviewers: dict[str, dict[str, Any]],
    reclassified_scope_ids: set[str],
    errors: list[str],
) -> None:
    compared_fields = (
        "status",
        "evidence_mode",
        "evidence",
        "guarantee",
        "reviewer_id",
    )
    for tombstone_id, tombstone in tombstones.items():
        where = f"scope_tombstones[{tombstone_id}]"
        unit_id = tombstone.get("origin_review_unit_id")
        unit = checkpoint_units.get(unit_id)
        if unit is None:
            errors.append(f"{where}.origin_review_unit_id: 観測checkpointにない確認単位です")
            continue
        if unit.get("scope_candidate_ids") != [tombstone.get("scope_candidate_id")]:
            errors.append(f"{where}.scope_candidate_id: 元の確認単位と一致しません")
        if unit.get("review_case_id") != tombstone.get("origin_review_case_id"):
            errors.append(f"{where}.origin_review_case_id: 元の確認単位と一致しません")
        for field in compared_fields:
            if tombstone.get(field) != unit.get(field):
                errors.append(f"{where}.{field}: 元の確認単位と一致しません")
        if tombstone.get("reviewer_id") not in checkpoint_reviewers:
            errors.append(f"{where}.reviewer_id: 観測checkpointにないreviewerです")
    retained_origin_ids = {
        tombstone.get("origin_review_unit_id") for tombstone in tombstones.values()
    }
    for unit_id, unit in checkpoint_units.items():
        refs = unit.get("scope_candidate_ids")
        if (
            list_value(refs)
            and len(refs) == 1
            and refs[0] in reclassified_scope_ids
            and unit_id not in retained_origin_ids
        ):
            errors.append(
                f"scope_tombstones: 再分類前の確認単位を履歴へ残してください: {unit_id}"
            )


def compare_discovery_baseline(
    baseline_manifest: dict[str, Any],
    baseline_units: dict[str, dict[str, Any]],
    baseline_reviewers: dict[str, dict[str, Any]],
    final_manifest: dict[str, Any],
    final_units: dict[str, dict[str, Any]],
    final_reviewers: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for label, baseline_items, final_items in (
        ("review_units", baseline_units, final_units),
        ("reviewers", baseline_reviewers, final_reviewers),
    ):
        if set(baseline_items) != set(final_items):
            errors.append(f"{label}: discovery baselineから追加・削除できません")
        for item_id in set(baseline_items) & set(final_items):
            if baseline_items[item_id] != final_items[item_id]:
                errors.append(
                    f"{label}[{item_id}]: discovery完了後に状態・証拠・担当を変更できません"
                )
    baseline_tombstones = require_unique_ids(
        baseline_manifest.get("scope_tombstones", []),
        "discovery baseline.scope_tombstones",
        errors,
    )
    final_tombstones = require_unique_ids(
        final_manifest.get("scope_tombstones", []), "scope_tombstones", errors
    )
    if set(baseline_tombstones) != set(final_tombstones):
        errors.append("scope_tombstones: discovery baselineから追加・削除できません")
    for tombstone_id in set(baseline_tombstones) & set(final_tombstones):
        if baseline_tombstones[tombstone_id] != final_tombstones[tombstone_id]:
            errors.append(
                f"scope_tombstones[{tombstone_id}]: discovery完了後にstatus・証拠・由来を変更できません"
            )


def validate_review_stage(
    manifest: dict[str, Any],
    scope_items: dict[str, dict[str, Any]],
    applicable: set[str],
    downstream: set[str],
    current_contracts: set[str],
    tombstones: dict[str, dict[str, Any]],
    *,
    stage: str,
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if manifest.get("discovery_gate") != "passed":
        errors.append("manifest.discovery_gate: passedである必要があります")
    if stage == "discovery":
        if manifest.get("state") != "discovery-complete":
            errors.append("manifest.state: discovery-completeである必要があります")
        if "candidate_gate" in manifest:
            errors.append("manifest.candidate_gate: discovery stageには置けません")
        if "finding_candidates" in manifest:
            errors.append("manifest.finding_candidates: discovery stageには置けません")
    else:
        if manifest.get("state") != "candidate-sorted":
            errors.append("manifest.state: candidate-sortedである必要があります")
        if manifest.get("candidate_gate") != "passed":
            errors.append("manifest.candidate_gate: passedである必要があります")

    units = require_unique_ids(manifest.get("review_units"), "review_units", errors)
    covered_cases: dict[tuple[str, str], int] = {}
    covered_review_cases: dict[str, int] = {}
    unit_signatures: dict[tuple[Any, ...], str] = {}
    for unit_id, unit in units.items():
        where = f"review_units[{unit_id}]"
        refs = unit.get("scope_candidate_ids")
        if not list_value(refs) or len(refs) != 1 or not all(text_value(value) for value in refs):
            errors.append(f"{where}.scope_candidate_ids: 一つのapplicable候補だけを指定してください")
        else:
            unknown = set(refs) - applicable
            if unknown:
                errors.append(f"{where}.scope_candidate_ids: applicable以外を参照しています: {sorted(unknown)}")

        require_text(unit, "contract", where, errors)
        require_text(unit, "reachable_path", where, errors)
        require_identifier(unit, "path_id", where, errors)
        require_identifier(unit, "review_case_id", where, errors)
        require_text(unit, "boundary", where, errors)
        require_text(unit, "evidence", where, errors)
        require_text(unit, "guarantee", where, errors)
        require_identifier(unit, "reviewer_id", where, errors)
        if unit.get("status") not in UNIT_STATES:
            errors.append(f"{where}.status: {sorted(UNIT_STATES)} のいずれかが必要です")
        if unit.get("evidence_mode") not in EVIDENCE_MODES:
            errors.append(f"{where}.evidence_mode: {sorted(EVIDENCE_MODES)} のいずれかが必要です")
        if list_value(refs) and len(refs) == 1 and refs[0] in scope_items:
            scope_item = scope_items[refs[0]]
            if unit.get("contract") != scope_item.get("contract"):
                errors.append(f"{where}.contract: scope候補の契約と一致しません")
            if unit.get("path_id") != scope_item.get("path_id"):
                errors.append(f"{where}.path_id: scope候補のpath_idと一致しません")
            case_id = unit.get("review_case_id")
            if case_id not in scope_item.get("review_case_ids", []):
                errors.append(f"{where}.review_case_id: scope Gateにない確認caseです")
            elif text_value(case_id):
                case_key = (refs[0], case_id)
                covered_cases[case_key] = covered_cases.get(case_key, 0) + 1
                covered_review_cases[case_id] = covered_review_cases.get(case_id, 0) + 1

        signature = (
            refs[0] if list_value(refs) and len(refs) == 1 else None,
            unit.get("review_case_id"),
        )
        previous_id = unit_signatures.get(signature)
        if previous_id is not None:
            errors.append(
                f"{where}: 同じscope確認caseが重複しています: {previous_id}"
            )
        else:
            unit_signatures[signature] = unit_id

    for case_id, count in sorted(covered_review_cases.items()):
        if count > 1:
            errors.append(
                "review_units: 同じ確認caseを複数の確認単位へ割り当てられません: "
                f"{case_id} ({count}件)"
            )

    for scope_id in sorted(applicable):
        for case_id in scope_items[scope_id].get("review_case_ids", []):
            count = covered_cases.get((scope_id, case_id), 0)
            if count != 1:
                errors.append(
                    "review_units: scope Gateで固定した確認caseは一つの単位で確認してください: "
                    f"{scope_id}/{case_id} ({count}件)"
                )

    reviewers = require_unique_ids(manifest.get("reviewers"), "reviewers", errors)
    if not reviewers:
        errors.append("reviewers: 1件以上必要です")
    for reviewer_id, reviewer in reviewers.items():
        where = f"reviewers[{reviewer_id}]"
        status = reviewer.get("status")
        if status not in REVIEWER_STATES:
            errors.append(f"{where}.status: completedまたはreassignedが必要です")
        if status == "reassigned":
            require_identifier(reviewer, "transferred_to", where, errors)

    completed_reviewers = {
        reviewer_id for reviewer_id, reviewer in reviewers.items() if reviewer.get("status") == "completed"
    }
    for reviewer_id, reviewer in reviewers.items():
        if reviewer.get("status") != "reassigned":
            continue
        transferred_to = reviewer.get("transferred_to")
        if transferred_to not in completed_reviewers:
            errors.append(
                f"reviewers[{reviewer_id}].transferred_to: completedのreviewerを指定してください"
            )
    for unit_id, unit in units.items():
        if unit.get("reviewer_id") not in completed_reviewers:
            errors.append(
                f"review_units[{unit_id}].reviewer_id: completedのreviewerを指定してください"
            )

    if stage == "discovery":
        return units, reviewers

    candidates = require_unique_ids(manifest.get("finding_candidates", []), "finding_candidates", errors)
    blocking_coverage: dict[str, int] = {}
    tombstone_coverage: dict[str, int] = {}
    downstream_coverage: dict[str, int] = {}
    candidate_signatures: set[tuple[Any, ...]] = set()
    for candidate_id, candidate in candidates.items():
        where = f"finding_candidates[{candidate_id}]"
        routing = candidate.get("routing")
        if routing not in ROUTINGS:
            errors.append(f"{where}.routing: {sorted(ROUTINGS)} のいずれかが必要です")
            continue
        if candidate.get("validity") not in {"valid", "invalid"}:
            errors.append(f"{where}.validity: validまたはinvalidが必要です")
        if candidate.get("gate_effect") not in {"blocks", "does-not-block"}:
            errors.append(f"{where}.gate_effect: blocksまたはdoes-not-blockが必要です")
        require_text(candidate, "reason", where, errors)

        referenced_units: set[str] = set()
        if routing in {"fix-here", "contract-decision", "not-applicable", "later-gate"}:
            refs = candidate.get("review_unit_ids")
            if not list_value(refs) or not refs or not all(text_value(value) for value in refs):
                errors.append(f"{where}.review_unit_ids: 空でない文字列の配列が必要です")
            elif len(set(refs)) != len(refs):
                errors.append(f"{where}.review_unit_ids: 重複した確認単位があります")
            else:
                allowed_ids = set(units)
                if routing == "not-applicable":
                    allowed_ids |= set(tombstones)
                unknown = set(refs) - allowed_ids
                if unknown:
                    errors.append(f"{where}.review_unit_ids: 不明な確認単位です: {sorted(unknown)}")
                referenced_units = set(refs) & allowed_ids

        conflicts_for_signature = candidate.get("conflicting_contracts", [])
        signature = (
            routing,
            tuple(sorted(referenced_units)),
            candidate.get("downstream_scope_candidate_id"),
            tuple(sorted(conflicts_for_signature))
            if list_value(conflicts_for_signature)
            and all(text_value(value) for value in conflicts_for_signature)
            else (),
        )
        if signature in candidate_signatures:
            errors.append(f"{where}: 同じ確認単位と振り分けの候補が重複しています")
        candidate_signatures.add(signature)

        if routing == "fix-here":
            if candidate.get("validity") != "valid" or candidate.get("gate_effect") != "blocks":
                errors.append(f"{where}: fix-hereはvalidかつblocksである必要があります")
            if referenced_units and any(
                units[unit_id].get("status") != "violated" for unit_id in referenced_units
            ):
                errors.append(f"{where}: fix-hereはviolatedの確認単位だけを参照してください")
            for unit_id in referenced_units:
                if units[unit_id].get("status") == "violated":
                    blocking_coverage[unit_id] = blocking_coverage.get(unit_id, 0) + 1
        elif routing == "later-gate":
            if candidate.get("validity") != "valid":
                errors.append(f"{where}: later-gateはvalidである必要があります")
            if candidate.get("gate_effect") != "does-not-block":
                errors.append(f"{where}: later-gateは現在Gateをblockできません")
            scope_id = candidate.get("downstream_scope_candidate_id")
            if scope_id not in downstream:
                errors.append(f"{where}.downstream_scope_candidate_id: 明示済み後工程を参照してください")
            else:
                producer_scope_id = scope_items[scope_id].get("handoff_review_scope_candidate_id")
                producer_units = {
                    unit_id
                    for unit_id, unit in units.items()
                    if unit.get("scope_candidate_ids") == [producer_scope_id]
                }
                if not (referenced_units & producer_units):
                    errors.append(f"{where}.review_unit_ids: handoff面を確認した単位が必要です")
                if referenced_units - producer_units:
                    errors.append(f"{where}.review_unit_ids: handoff面以外の単位を混在できません")
                downstream_coverage[scope_id] = downstream_coverage.get(scope_id, 0) + 1
        elif routing == "contract-decision":
            conflicts = candidate.get("conflicting_contracts")
            if (
                not list_value(conflicts)
                or not all(text_value(value) for value in conflicts)
                or len(set(conflicts)) < 2
            ):
                errors.append(f"{where}.conflicting_contracts: 衝突する既存契約を2件以上指定してください")
            elif not set(conflicts).issubset(current_contracts):
                errors.append(f"{where}.conflicting_contracts: current_contractsにない契約を含められません")
            if candidate.get("validity") != "valid" or candidate.get("gate_effect") != "blocks":
                errors.append(f"{where}: contract-decisionはvalidかつblocksである必要があります")
            if referenced_units and any(
                units[unit_id].get("status") not in {"violated", "unverified"}
                for unit_id in referenced_units
            ):
                errors.append(
                    f"{where}: contract-decisionはviolatedまたはunverifiedの単位だけを参照してください"
                )
            live_units = [units[unit_id] for unit_id in referenced_units if unit_id in units]
            if list_value(conflicts) and all(text_value(value) for value in conflicts):
                referenced_contracts = {unit.get("contract") for unit in live_units}
                if not set(conflicts).issubset(referenced_contracts):
                    errors.append(f"{where}: 衝突契約ごとの確認単位を参照してください")
            path_ids = {unit.get("path_id") for unit in live_units}
            if len(path_ids) != 1:
                errors.append(f"{where}: 衝突契約は同じpath_id上にある必要があります")
            require_text(candidate, "reachable_scenario", where, errors)
            for unit_id in referenced_units:
                if units[unit_id].get("status") in {"violated", "unverified"}:
                    blocking_coverage[unit_id] = blocking_coverage.get(unit_id, 0) + 1
        else:
            if candidate.get("validity") != "invalid":
                errors.append(f"{where}: not-applicableは現在レビューではinvalidである必要があります")
            if candidate.get("gate_effect") != "does-not-block":
                errors.append(f"{where}: not-applicableは現在Gateをblockできません")
            live_refs = referenced_units & set(units)
            if live_refs:
                errors.append(f"{where}: not-applicableはscope_tombstoneだけを参照してください")
            for unit_id in referenced_units & set(tombstones):
                tombstone_coverage[unit_id] = tombstone_coverage.get(unit_id, 0) + 1

    blocking_units = {
        unit_id
        for unit_id, unit in units.items()
        if unit.get("status") in {"violated", "unverified"}
    }
    for unit_id in sorted(blocking_units):
        count = blocking_coverage.get(unit_id, 0)
        if count != 1:
            errors.append(
                f"finding_candidates: violated/unverified単位は一つの候補へ統合してください: {unit_id} ({count}件)"
            )
    routed_tombstones = {
        tombstone_id
        for tombstone_id, tombstone in tombstones.items()
        if tombstone.get("status") == "violated"
    }
    for tombstone_id in sorted(routed_tombstones):
        count = tombstone_coverage.get(tombstone_id, 0)
        if count != 1:
            errors.append(
                f"finding_candidates: scope-outした違反は一つのnot-applicable候補へ統合してください: {tombstone_id} ({count}件)"
            )
    for scope_id, count in sorted(downstream_coverage.items()):
        if count != 1:
            errors.append(
                f"finding_candidates: 同じ後工程候補を重複登録できません: {scope_id} ({count}件)"
            )
    return units, reviewers


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
            "review-gate: review input・brief・manifestのrootはobjectである必要があります",
            file=sys.stderr,
        )
        return 2

    errors: list[str] = []
    (
        review_id,
        condition_ids,
        input_contracts,
        input_handoffs,
        input_seeds,
        _,
        previous_brief_digest,
    ) = validate_review_input(review_input, errors)
    current_contracts, handoffs, seeds, current_case_owners = validate_brief(
        brief,
        errors,
        expected_review_id=review_id,
        expected_condition_ids=condition_ids,
        expected_contracts=input_contracts,
    )
    validate_coverage_baseline_match(
        input_handoffs,
        input_seeds,
        handoffs,
        seeds,
        errors,
    )
    validate_brief_revision_shape(brief, "brief", errors)

    revision = brief.get("revision")
    valid_revision = (
        isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1
    )
    if revision == 1 and not isinstance(revision, bool):
        if args.previous_brief:
            errors.append("--previous-brief: Brief revision 1では指定できません")
        if previous_brief_digest is not None:
            errors.append(
                "review_input.previous_brief_digest: Brief revision 1ではnullが必要です"
            )
    elif valid_revision:
        if (
            not isinstance(previous_brief_digest, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", previous_brief_digest) is None
        ):
            errors.append(
                "review_input.previous_brief_digest: sha256:<64桁の小文字16進数>が必要です"
            )
        if not args.previous_brief:
            errors.append(
                f"--previous-brief: Brief revision {revision}では必須です"
            )
        else:
            try:
                previous_brief = load_json(args.previous_brief)
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"previous Briefを読めません: {error}")
                previous_brief = None
            if not isinstance(previous_brief, dict):
                errors.append("previous Briefのrootはobjectである必要があります")
            else:
                previous_errors: list[str] = []
                (
                    _,
                    _,
                    _,
                    previous_case_owners,
                ) = validate_brief(previous_brief, previous_errors)
                validate_brief_revision_shape(
                    previous_brief, "previous Brief", previous_errors
                )
                if previous_brief.get("review_id") != brief.get("review_id"):
                    previous_errors.append(
                        "previous Brief.review_id: 現Briefと一致しません"
                    )
                previous_revision = previous_brief.get("revision")
                if (
                    isinstance(previous_revision, bool)
                    or not isinstance(previous_revision, int)
                    or previous_revision != revision - 1
                ):
                    previous_errors.append(
                        "previous Brief.revision: 現Briefの直前revisionである必要があります"
                    )
                actual_previous_digest = canonical_json_digest(previous_brief)
                if previous_brief_digest != actual_previous_digest:
                    errors.append(
                        "review_input.previous_brief_digest: 実際に渡した直前Briefのdigestと一致しません"
                    )
                migration_errors: list[str] = []
                validate_review_case_migrations(
                    brief,
                    previous_case_owners,
                    current_case_owners,
                    migration_errors,
                )
                errors.extend(
                    f"previous Brief: {error}" for error in previous_errors
                )
                errors.extend(
                    f"current Brief migration: {error}"
                    for error in migration_errors
                )
    scope_items, applicable, downstream = validate_scope(
        manifest, brief, current_contracts, handoffs, seeds, errors
    )
    if args.stage != "scope" and args.previous_scope_baseline:
        errors.append("--previous-scope-baseline: scope stageでだけ使用できます")
    if args.stage != "scope" and args.observation_checkpoint:
        errors.append("--observation-checkpoint: scope stageでだけ使用できます")
    if args.observation_checkpoint and not args.previous_scope_baseline:
        errors.append(
            "--observation-checkpoint: --previous-scope-baselineと一緒に使用してください"
        )
    if args.stage != "candidate" and args.discovery_baseline:
        errors.append("--discovery-baseline: candidate stageでだけ使用できます")

    if args.stage == "scope":
        if manifest.get("state") != "scope-fixed":
            errors.append("manifest.state: scope-fixedである必要があります")
        validate_scope_stage_shape(
            manifest, is_rescope=bool(args.previous_scope_baseline), errors=errors
        )
        if not args.previous_scope_baseline:
            validate_tombstones(manifest, scope_items, errors)
        else:
            try:
                previous_scope = load_json(args.previous_scope_baseline)
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"previous scope baselineを読めません: {error}")
                previous_scope = None
            if not isinstance(previous_scope, dict):
                errors.append("previous scope baselineのrootはobjectである必要があります")
            else:
                previous_errors: list[str] = []
                previous_items, _, _ = validate_scope(
                    previous_scope,
                    brief,
                    current_contracts,
                    handoffs,
                    seeds,
                    previous_errors,
                )
                if previous_scope.get("state") != "scope-fixed":
                    previous_errors.append(
                        "previous scope baseline.state: scope-fixedである必要があります"
                    )
                validate_scope_stage_shape(
                    previous_scope, is_rescope=True, errors=previous_errors
                )
                errors.extend(
                    f"previous scope baseline: {error}" for error in previous_errors
                )
                previous_tombstones = validate_tombstones(
                    previous_scope, previous_items, errors
                )
                current_tombstones = validate_scope_transition(
                    previous_scope,
                    previous_items,
                    manifest,
                    scope_items,
                    allow_scope_changes=True,
                    errors=errors,
                )
                new_tombstone_ids = set(current_tombstones) - set(previous_tombstones)
                reclassified_scope_ids = {
                    scope_id
                    for scope_id, previous_item in previous_items.items()
                    if previous_item.get("classification") == "applicable"
                    and scope_items.get(scope_id, {}).get("classification") != "applicable"
                }
                if new_tombstone_ids and not args.observation_checkpoint:
                    errors.append(
                        "--observation-checkpoint: applicableを再分類するtombstone追加時は必須です"
                    )
                elif not new_tombstone_ids and args.observation_checkpoint:
                    errors.append(
                        "--observation-checkpoint: 新しいtombstoneがないscope更新には不要です"
                    )
                elif new_tombstone_ids and args.observation_checkpoint:
                    try:
                        checkpoint = load_json(args.observation_checkpoint)
                    except (OSError, json.JSONDecodeError) as error:
                        errors.append(f"observation checkpointを読めません: {error}")
                        checkpoint = None
                    if not isinstance(checkpoint, dict):
                        errors.append("observation checkpointのrootはobjectである必要があります")
                    else:
                        checkpoint_errors: list[str] = []
                        checkpoint_items, checkpoint_applicable, _ = validate_scope(
                            checkpoint,
                            brief,
                            current_contracts,
                            handoffs,
                            seeds,
                            checkpoint_errors,
                        )
                        validate_scope_transition(
                            previous_scope,
                            previous_items,
                            checkpoint,
                            checkpoint_items,
                            allow_scope_changes=False,
                            errors=checkpoint_errors,
                        )
                        checkpoint_units, checkpoint_reviewers = validate_observation_checkpoint(
                            checkpoint,
                            checkpoint_items,
                            checkpoint_applicable,
                            reclassified_scope_ids,
                            checkpoint_errors,
                        )
                        validate_tombstone_origins(
                            {
                                tombstone_id: current_tombstones[tombstone_id]
                                for tombstone_id in new_tombstone_ids
                            },
                            checkpoint_units,
                            checkpoint_reviewers,
                            reclassified_scope_ids,
                            checkpoint_errors,
                        )
                        errors.extend(
                            f"observation checkpoint: {error}"
                            for error in checkpoint_errors
                        )
    else:
        scope_baseline: dict[str, Any] | None = None
        baseline_items: dict[str, dict[str, Any]] = {}
        baseline_tombstones: dict[str, dict[str, Any]] = {}
        if not args.scope_baseline:
            errors.append(f"--scope-baseline: {args.stage} stageでは必須です")
        else:
            try:
                loaded_scope = load_json(args.scope_baseline)
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"scope baselineを読めません: {error}")
                loaded_scope = None
            if not isinstance(loaded_scope, dict):
                errors.append("scope baselineのrootはobjectである必要があります")
            else:
                scope_baseline = loaded_scope
                baseline_errors: list[str] = []
                baseline_items, _, _ = validate_scope(
                    scope_baseline,
                    brief,
                    current_contracts,
                    handoffs,
                    seeds,
                    baseline_errors,
                )
                if scope_baseline.get("state") != "scope-fixed":
                    baseline_errors.append("scope baseline.state: scope-fixedである必要があります")
                validate_scope_stage_shape(
                    scope_baseline, is_rescope=True, errors=baseline_errors
                )
                errors.extend(f"scope baseline: {error}" for error in baseline_errors)
                baseline_tombstones = validate_scope_transition(
                    scope_baseline,
                    baseline_items,
                    manifest,
                    scope_items,
                    allow_scope_changes=False,
                    errors=errors,
                )

        if args.stage == "discovery":
            validate_review_stage(
                manifest,
                scope_items,
                applicable,
                downstream,
                current_contracts,
                baseline_tombstones,
                stage="discovery",
                errors=errors,
            )
        else:
            discovery_baseline: dict[str, Any] | None = None
            discovery_units: dict[str, dict[str, Any]] = {}
            discovery_reviewers: dict[str, dict[str, Any]] = {}
            if not args.discovery_baseline:
                errors.append("--discovery-baseline: candidate stageでは必須です")
            else:
                try:
                    loaded_discovery = load_json(args.discovery_baseline)
                except (OSError, json.JSONDecodeError) as error:
                    errors.append(f"discovery baselineを読めません: {error}")
                    loaded_discovery = None
                if not isinstance(loaded_discovery, dict):
                    errors.append("discovery baselineのrootはobjectである必要があります")
                else:
                    discovery_baseline = loaded_discovery
                    discovery_errors: list[str] = []
                    discovery_items, discovery_applicable, discovery_downstream = validate_scope(
                        discovery_baseline,
                        brief,
                        current_contracts,
                        handoffs,
                        seeds,
                        discovery_errors,
                    )
                    discovery_tombstones: dict[str, dict[str, Any]] = {}
                    if scope_baseline is not None:
                        discovery_tombstones = validate_scope_transition(
                            scope_baseline,
                            baseline_items,
                            discovery_baseline,
                            discovery_items,
                            allow_scope_changes=False,
                            errors=discovery_errors,
                        )
                    discovery_units, discovery_reviewers = validate_review_stage(
                        discovery_baseline,
                        discovery_items,
                        discovery_applicable,
                        discovery_downstream,
                        current_contracts,
                        discovery_tombstones,
                        stage="discovery",
                        errors=discovery_errors,
                    )
                    errors.extend(
                        f"discovery baseline: {error}" for error in discovery_errors
                    )

            final_units, final_reviewers = validate_review_stage(
                manifest,
                scope_items,
                applicable,
                downstream,
                current_contracts,
                baseline_tombstones,
                stage="candidate",
                errors=errors,
            )
            if discovery_baseline is not None:
                compare_discovery_baseline(
                    discovery_baseline,
                    discovery_units,
                    discovery_reviewers,
                    manifest,
                    final_units,
                    final_reviewers,
                    errors,
                )

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"review-gate: {args.stage} gate ok; "
        f"brief_digest={canonical_json_digest(brief)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
