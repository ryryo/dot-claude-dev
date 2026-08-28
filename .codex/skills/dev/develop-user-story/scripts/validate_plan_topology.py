#!/usr/bin/env python3
"""Validate the structural exit conditions of Parallelization Topology Gate.

The validator proves that the declared execution waves match the earliest DAG
waves and that concurrently runnable lanes do not share writable resources. It
does not decide whether a stated dependency is semantically necessary; the
independent PLAN reviewer owns that judgment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath
from typing import Any


START = "<!-- parallelization-topology:start -->"
END = "<!-- parallelization-topology:end -->"
EDGE_CLASSES = {
    "hard-dependency",
    "shared-seam",
    "join",
    "external-stop",
    "serialized-exception",
}
EXECUTIONS = {"local", "external"}
ALTERNATIVES = {"narrow-scope", "shared-seam", "join-only"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PLANのParallelization Topology Gate manifestを検証する"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="repository root。既定はcurrent directory",
    )
    parser.add_argument("plan", help="integration／coordination PLAN Markdown path")
    return parser.parse_args()


def text_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_text(item: dict[str, Any], key: str, where: str, errors: list[str]) -> None:
    if not text_value(item.get(key)):
        errors.append(f"{where}.{key}: 空でない文字列が必要です")


def extract_manifest(plan_path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        source = plan_path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"PLANを読めません: {error}")
        return {}

    pattern = re.compile(
        rf"{re.escape(START)}\s*```json\s*(.*?)\s*```\s*{re.escape(END)}",
        re.DOTALL,
    )
    matches = pattern.findall(source)
    if len(matches) != 1:
        errors.append(
            "Parallelization Topology Gate manifest blockは正しいmarker間に1個だけ必要です"
        )
        return {}
    try:
        manifest = json.loads(matches[0])
    except json.JSONDecodeError as error:
        errors.append(f"manifest JSONが不正です: {error}")
        return {}
    if not isinstance(manifest, dict):
        errors.append("manifest: objectが必要です")
        return {}
    return manifest


def valid_relative_path(value: Any, *, allow_scope: bool) -> bool:
    if not text_value(value) or "\\" in value:
        return False
    scope = value.strip()
    if allow_scope:
        if scope.endswith("/**"):
            scope = scope[:-3]
        if any(marker in scope for marker in ("*", "?", "[", "]")):
            return False
    elif any(marker in scope for marker in ("*", "?", "[", "]")):
        return False
    if not scope or scope.endswith("/"):
        return False
    path = PurePosixPath(scope)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def section_heading_exists(plan_path: Path, section: str) -> bool:
    try:
        source = plan_path.read_text(encoding="utf-8")
    except OSError:
        return False
    source = re.sub(r"<!--.*?-->", "", source, flags=re.DOTALL)
    headings: list[str] = []
    fence_character: str | None = None
    for line in source.splitlines():
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            character = fence.group(1)[0]
            if fence_character is None:
                fence_character = character
            elif fence_character == character:
                fence_character = None
            continue
        if fence_character is not None:
            continue
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            headings.append(heading.group(1))
    for heading in headings:
        normalized = heading.strip()
        if normalized == section:
            return True
        if normalized.startswith(section):
            suffix = normalized[len(section) :]
            if suffix and suffix[0] in " \t:：—–-／/":
                return True
    return False


def scope_parts(scope: str) -> tuple[str, bool]:
    normalized = scope.strip().rstrip("/")
    if normalized.endswith("/**"):
        return normalized[:-3].rstrip("/"), True
    return normalized, False


def scope_overlap(left: str, right: str) -> bool:
    left_path, left_tree = scope_parts(left)
    right_path, right_tree = scope_parts(right)
    if left_path == right_path:
        return True
    if left_tree and right_path.startswith(f"{left_path}/"):
        return True
    if right_tree and left_path.startswith(f"{right_path}/"):
        return True
    return False


def shared_resources(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    resources: set[str] = set()
    left_scopes = left.get("writeScopes") if isinstance(left.get("writeScopes"), list) else []
    right_scopes = right.get("writeScopes") if isinstance(right.get("writeScopes"), list) else []
    for left_scope in left_scopes:
        if not isinstance(left_scope, str):
            continue
        for right_scope in right_scopes:
            if not isinstance(right_scope, str):
                continue
            if scope_overlap(left_scope, right_scope):
                left_path, left_tree = scope_parts(left_scope)
                right_path, right_tree = scope_parts(right_scope)
                if left_path == right_path:
                    resources.add(left_scope if left_tree else right_scope)
                elif left_tree:
                    resources.add(right_scope)
                elif right_tree:
                    resources.add(left_scope)
    left_states = left.get("externalStates") if isinstance(left.get("externalStates"), list) else []
    right_states = right.get("externalStates") if isinstance(right.get("externalStates"), list) else []
    for state in set(item for item in left_states if isinstance(item, str)) & set(
        item for item in right_states if isinstance(item, str)
    ):
        resources.add(f"external:{state}")
    return sorted(resources)


def index_objects(value: Any, where: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{where}: 配列が必要です")
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(value):
        location = f"{where}[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{location}: objectが必要です")
            continue
        item_id = raw.get("id")
        if not text_value(item_id):
            errors.append(f"{location}.id: 空でない文字列が必要です")
            continue
        if item_id in indexed:
            errors.append(f"{location}.id: 重複しています: {item_id}")
            continue
        indexed[item_id] = raw
    return indexed


def validate_lane(
    lane_id: str, lane: dict[str, Any], root: Path, errors: list[str]
) -> None:
    where = f"lanes[{lane_id}]"
    require_text(lane, "plan", where, errors)
    require_text(lane, "section", where, errors)
    if text_value(lane.get("plan")):
        if not valid_relative_path(lane["plan"], allow_scope=False):
            errors.append(f"{where}.plan: wildcardや上位参照のないrelative pathが必要です")
        else:
            lane_plan_path = root / lane["plan"]
            if not inside_root(lane_plan_path, root):
                errors.append(f"{where}.plan: symlink解決後にrepository root外を参照しています")
            elif not lane_plan_path.is_file():
                errors.append(f"{where}.plan: PLAN fileが存在しません: {lane['plan']}")
            elif text_value(lane.get("section")) and not section_heading_exists(
                lane_plan_path, lane["section"]
            ):
                errors.append(
                    f"{where}.section: PLAN内に対応する見出しがありません: {lane['section']}"
                )
    if lane.get("execution") not in EXECUTIONS:
        errors.append(f"{where}.execution: {sorted(EXECUTIONS)} のいずれかが必要です")

    scopes = lane.get("writeScopes")
    if not isinstance(scopes, list) or not scopes:
        errors.append(f"{where}.writeScopes: 1件以上の配列が必要です")
        scopes = []
    for index, scope in enumerate(scopes):
        if not valid_relative_path(scope, allow_scope=True):
            errors.append(
                f"{where}.writeScopes[{index}]: relative file pathか末尾/**のdirectory scopeが必要です"
            )
    if len(scopes) != len(set(scope for scope in scopes if isinstance(scope, str))):
        errors.append(f"{where}.writeScopes: 重複があります")

    states = lane.get("externalStates")
    if not isinstance(states, list) or not all(text_value(state) for state in states):
        errors.append(f"{where}.externalStates: 文字列の配列が必要です")
        states = []
    if len(states) != len(set(state for state in states if isinstance(state, str))):
        errors.append(f"{where}.externalStates: 重複があります")
    if lane.get("execution") == "external" and not states:
        errors.append(f"{where}.externalStates: external laneでは1件以上必要です")


def validate_edge(
    edge: dict[str, Any],
    index: int,
    lanes: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[str | None, str | None]:
    where = f"edges[{index}]"
    require_text(edge, "from", where, errors)
    require_text(edge, "to", where, errors)
    require_text(edge, "reason", where, errors)
    require_text(edge, "evidence", where, errors)
    require_text(edge, "handoff", where, errors)
    source = edge.get("from")
    target = edge.get("to")
    if source not in lanes:
        errors.append(f"{where}.from: lanesにないIDです: {source}")
    if target not in lanes:
        errors.append(f"{where}.to: lanesにないIDです: {target}")
    if source == target and text_value(source):
        errors.append(f"{where}: 自己依存は許可されません")
    classification = edge.get("classification")
    if classification not in EDGE_CLASSES:
        errors.append(f"{where}.classification: {sorted(EDGE_CLASSES)} のいずれかが必要です")

    if source in lanes and target in lanes and source != target:
        resources = shared_resources(lanes[source], lanes[target])
        if resources and classification != "serialized-exception":
            errors.append(
                f"{where}: writer重複 {resources} はserialized-exceptionとして代替案を審査してください"
            )
        if classification == "serialized-exception":
            if not resources:
                errors.append(f"{where}: writer重複のないedgeをserialized-exceptionにできません")
            validate_serialized_exception(edge, where, resources, errors)
    return source if isinstance(source, str) else None, target if isinstance(target, str) else None


def validate_serialized_exception(
    edge: dict[str, Any], where: str, actual_resources: list[str], errors: list[str]
) -> None:
    resources = edge.get("resources")
    if not isinstance(resources, list) or not resources or not all(text_value(item) for item in resources):
        errors.append(f"{where}.resources: writer重複を示す空でない文字列の配列が必要です")
    else:
        for resource in actual_resources:
            if resource not in resources:
                errors.append(f"{where}.resources: 実際のwriter重複が未記載です: {resource}")
    require_text(edge, "criticalPathImpact", where, errors)
    alternatives = edge.get("alternatives")
    if not isinstance(alternatives, dict):
        errors.append(f"{where}.alternatives: objectが必要です")
        return
    for alternative in sorted(ALTERNATIVES):
        if not text_value(alternatives.get(alternative)):
            errors.append(f"{where}.alternatives.{alternative}: 棄却理由が必要です")


def topological_levels(
    lane_ids: set[str], edges: list[tuple[str, str]], errors: list[str]
) -> dict[str, int] | None:
    incoming = {lane_id: 0 for lane_id in lane_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    predecessors: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        incoming[target] += 1
        outgoing[source].append(target)
        predecessors[target].append(source)

    queue = deque(sorted(lane_id for lane_id, degree in incoming.items() if degree == 0))
    order: list[str] = []
    while queue:
        lane_id = queue.popleft()
        order.append(lane_id)
        for target in sorted(outgoing[lane_id]):
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    if len(order) != len(lane_ids):
        errors.append("edges: 依存DAGに閉路があります")
        return None

    levels: dict[str, int] = {}
    for lane_id in order:
        levels[lane_id] = 0 if not predecessors[lane_id] else 1 + max(
            levels[source] for source in predecessors[lane_id]
        )
    return levels


def validate_waves(
    raw_waves: Any,
    lanes: dict[str, dict[str, Any]],
    levels: dict[str, int],
    errors: list[str],
) -> tuple[list[list[str]], int]:
    waves = index_objects(raw_waves, "waves", errors)
    declared: list[list[str]] = []
    seen: set[str] = set()
    for wave_id, wave in waves.items():
        where = f"waves[{wave_id}]"
        lane_ids = wave.get("lanes")
        if not isinstance(lane_ids, list) or not lane_ids or not all(text_value(item) for item in lane_ids):
            errors.append(f"{where}.lanes: 空でないlane IDの配列が必要です")
            lane_ids = []
        if len(lane_ids) != len(set(lane_ids)):
            errors.append(f"{where}.lanes: 重複があります")
        for lane_id in lane_ids:
            if lane_id not in lanes:
                errors.append(f"{where}.lanes: 未定義laneです: {lane_id}")
            if lane_id in seen:
                errors.append(f"{where}.lanes: 複数waveにあるlaneです: {lane_id}")
            seen.add(lane_id)
        declared.append(lane_ids)

    missing = set(lanes) - seen
    if missing:
        errors.append(f"waves: 未配置laneがあります: {sorted(missing)}")

    expected: list[list[str]] = []
    if levels:
        for level in range(max(levels.values()) + 1):
            expected.append(sorted(lane_id for lane_id, value in levels.items() if value == level))
    normalized_declared = [sorted(wave) for wave in declared]
    if normalized_declared != expected:
        errors.append(
            f"waves: DAGの最早waveと一致しません: declared={normalized_declared}, expected={expected}"
        )

    for index, lane_ids in enumerate(declared):
        for left_index, left_id in enumerate(lane_ids):
            if left_id not in lanes:
                continue
            for right_id in lane_ids[left_index + 1 :]:
                if right_id not in lanes:
                    continue
                resources = shared_resources(lanes[left_id], lanes[right_id])
                for resource in resources:
                    kind = "external state" if resource.startswith("external:") else "write scope"
                    errors.append(
                        f"waves[{index}]: {left_id} と {right_id} の{kind}が重複しています: {resource}"
                    )

    max_local = max(
        (
            sum(
                1
                for lane_id in lane_ids
                if lane_id in lanes and lanes[lane_id].get("execution") == "local"
            )
            for lane_ids in declared
        ),
        default=0,
    )
    return declared, max_local


def validate(
    manifest: dict[str, Any], plan_path: Path, root: Path, errors: list[str]
) -> tuple[int, int, int]:
    if manifest.get("schemaVersion") != 1:
        errors.append("manifest.schemaVersion: 1である必要があります")
    if manifest.get("gate") != "parallelization-topology":
        errors.append("manifest.gate: parallelization-topologyである必要があります")
    require_text(manifest, "integrationPlan", "manifest", errors)
    if text_value(manifest.get("integrationPlan")):
        if not valid_relative_path(manifest["integrationPlan"], allow_scope=False):
            errors.append("manifest.integrationPlan: relative PLAN pathが必要です")
        elif (root / manifest["integrationPlan"]).resolve() != plan_path.resolve():
            errors.append("manifest.integrationPlan: 検証対象PLANのrepository relative pathと一致しません")

    lanes = index_objects(manifest.get("lanes"), "lanes", errors)
    if not lanes:
        errors.append("lanes: 1件以上必要です")
    for lane_id, lane in lanes.items():
        validate_lane(lane_id, lane, root, errors)

    section_owners: dict[tuple[str, str], str] = {}
    for lane_id, lane in lanes.items():
        if not text_value(lane.get("plan")) or not text_value(lane.get("section")):
            continue
        if not valid_relative_path(lane["plan"], allow_scope=False):
            continue
        key = (str((root / lane["plan"]).resolve()), lane["section"].strip())
        previous = section_owners.get(key)
        if previous is not None:
            errors.append(
                f"lanes[{lane_id}]: {previous} と同じPLAN sectionを所有できません: "
                f"{lane['plan']}#{lane['section']}"
            )
        else:
            section_owners[key] = lane_id

    raw_edges = manifest.get("edges")
    if not isinstance(raw_edges, list):
        errors.append("edges: 配列が必要です")
        raw_edges = []
    graph_edges: list[tuple[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    serialized_count = 0
    for index, raw in enumerate(raw_edges):
        if not isinstance(raw, dict):
            errors.append(f"edges[{index}]: objectが必要です")
            continue
        source, target = validate_edge(raw, index, lanes, errors)
        if raw.get("classification") == "serialized-exception":
            serialized_count += 1
        if source in lanes and target in lanes and source != target:
            pair = (source, target)
            if pair in seen_edges:
                errors.append(f"edges[{index}]: 重複edgeです: {source} -> {target}")
            else:
                seen_edges.add(pair)
                graph_edges.append(pair)

    levels = topological_levels(set(lanes), graph_edges, errors)
    max_local = 0
    if levels is not None:
        _, max_local = validate_waves(manifest.get("waves"), lanes, levels, errors)
    return len(lanes), max_local, serialized_count


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    root = Path(args.root).resolve()
    plan_path = Path(args.plan).resolve()
    if not root.is_dir():
        errors.append(f"repository rootが存在しません: {root}")
    elif not inside_root(plan_path, root):
        errors.append("検証対象PLANはsymlink解決後もrepository root配下にある必要があります")
    manifest = extract_manifest(plan_path, errors)
    lane_count = 0
    max_local = 0
    serialized_count = 0
    if manifest:
        lane_count, max_local, serialized_count = validate(
            manifest, plan_path, root, errors
        )
    if errors:
        for error in errors:
            print(f"plan-topology: error: {error}", file=sys.stderr)
        return 1
    print(
        "plan-topology: ok "
        f"({lane_count} lanes, local concurrency {max_local}, "
        f"serialized exceptions {serialized_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
