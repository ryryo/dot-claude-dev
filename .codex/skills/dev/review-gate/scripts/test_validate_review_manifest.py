#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


VALIDATOR = Path(__file__).with_name("validate_review_manifest.py")


def valid_review_input() -> dict:
    return review_input_for_brief(valid_brief())


def valid_brief() -> dict:
    return {
        "review_id": "review-1",
        "revision": 1,
        "review_case_migrations": [],
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
                "condition_id": "C1",
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


def canonical_digest(value: dict) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def review_input_for_brief(
    brief: dict, *, previous_brief: dict | None = None
) -> dict:
    return {
        "review_id": brief["review_id"],
        "condition_ids": [
            seed["condition_id"]
            for seed in brief["scope_seeds"]
            if seed.get("kind") == "condition"
        ],
        "current_contracts": copy.deepcopy(brief["current_contracts"]),
        "handoffs": copy.deepcopy(brief["handoffs"]),
        "scope_seeds": copy.deepcopy(brief["scope_seeds"]),
        "previous_brief_digest": (
            canonical_digest(previous_brief) if previous_brief is not None else None
        ),
    }


def valid_revised_brief() -> dict:
    brief = copy.deepcopy(valid_brief())
    brief["revision"] = 2
    brief["review_case_migrations"] = [
        {
            "previous_review_case_ids": ["C1-default"],
            "current_review_case_ids": ["C1-default"],
        },
        {
            "previous_review_case_ids": ["H1-snapshot"],
            "current_review_case_ids": ["H1-snapshot"],
        },
    ]
    return brief


def valid_manifest() -> dict:
    return {
        "review_id": "review-1",
        "brief_revision": 1,
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
        "review_id": manifest["review_id"],
        "brief_revision": manifest["brief_revision"],
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
    review_input: dict | None = None,
    brief: dict | None = None,
    previous_brief: dict | None = None,
    baseline: dict | None = None,
    discovery: dict | None = None,
    previous_scope: dict | None = None,
    observation: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        directory_path = Path(directory)
        resolved_brief = valid_brief() if brief is None else brief
        resolved_review_input = (
            review_input_for_brief(
                resolved_brief,
                previous_brief=(
                    previous_brief
                    if isinstance(resolved_brief.get("revision"), int)
                    and not isinstance(resolved_brief.get("revision"), bool)
                    and resolved_brief["revision"] > 1
                    else None
                ),
            )
            if review_input is None
            else review_input
        )
        review_input_path = directory_path / "review-input.json"
        review_input_path.write_text(
            json.dumps(resolved_review_input),
            encoding="utf-8",
        )
        brief_path = directory_path / "brief.json"
        brief_path.write_text(
            json.dumps(resolved_brief), encoding="utf-8"
        )
        command = [
            sys.executable,
            str(VALIDATOR),
            "--stage",
            stage,
            "--review-input",
            str(review_input_path),
            "--brief",
            str(brief_path),
        ]
        if previous_brief is not None:
            previous_brief_path = directory_path / "previous-brief.json"
            previous_brief_path.write_text(
                json.dumps(previous_brief), encoding="utf-8"
            )
            command.extend(["--previous-brief", str(previous_brief_path)])
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
    def test_review_input_argument_is_required(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--stage",
                "scope",
                "--brief",
                "brief.json",
            ],
            input="{}",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("--review-input", result.stderr)

    def test_review_input_allows_an_empty_condition_set(self) -> None:
        review_input = valid_review_input()
        review_input["condition_ids"] = []
        brief = valid_brief()
        brief["scope_seeds"][0]["kind"] = "invariant"
        del brief["scope_seeds"][0]["condition_id"]
        review_input = review_input_for_brief(brief)
        result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
            brief=brief,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_review_input_rejects_duplicate_conditions_and_contracts(self) -> None:
        review_input = valid_review_input()
        review_input["condition_ids"] = ["C1", "C1"]
        review_input["current_contracts"] = ["C1", "C1", "rendered output"]
        result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("review_input.condition_ids: 重複", result.stderr)
        self.assertIn("review_input.current_contracts: 重複", result.stderr)

    def test_review_input_requires_complete_handoff_and_seed_baseline(self) -> None:
        for field in ("handoffs", "scope_seeds"):
            with self.subTest(field=field):
                review_input = valid_review_input()
                del review_input[field]
                result = run_validator(
                    "scope",
                    scope_baseline(valid_manifest()),
                    review_input=review_input,
                )
                self.assertEqual(1, result.returncode)
                self.assertIn(f"review_input.{field}", result.stderr)

    def test_brief_cannot_add_or_change_review_input_coverage(self) -> None:
        review_input = valid_review_input()
        brief = valid_brief()
        brief["scope_seeds"].append(
            {
                "id": "invented-surface",
                "kind": "changed-surface",
                "source": "invented caller",
                "contract": "C1",
                "coverage_obligation": "classify-only",
                "review_case_ids": ["invented-case"],
            }
        )
        added = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
            brief=brief,
        )
        self.assertEqual(1, added.returncode)
        self.assertIn("Review Inputのseed ID集合", added.stderr)

        changed = valid_brief()
        changed["handoffs"][0]["owner"] = "different owner"
        changed_result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
            brief=changed,
        )
        self.assertEqual(1, changed_result.returncode)
        self.assertIn("handoffs[H1].owner", changed_result.stderr)

        changed_case = valid_brief()
        changed_case["scope_seeds"][0]["review_case_ids"] = ["different-case"]
        case_result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
            brief=changed_case,
        )
        self.assertEqual(1, case_result.returncode)
        self.assertIn("Review Inputのcase集合", case_result.stderr)

    def test_identifier_and_set_values_reject_surrounding_whitespace(self) -> None:
        mutations = (
            lambda value: value.update(review_id=" review-1"),
            lambda value: value.update(condition_ids=[" C1"]),
            lambda value: value.update(
                current_contracts=["C1", "rendered output "]
            ),
            lambda value: value["handoffs"][0].update(id=" H1"),
            lambda value: value["scope_seeds"][0].update(condition_id="C1 "),
            lambda value: value["scope_seeds"][0].update(
                review_case_ids=[" C1-default"]
            ),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                review_input = valid_review_input()
                mutate(review_input)
                result = run_validator(
                    "scope",
                    scope_baseline(valid_manifest()),
                    review_input=review_input,
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("前後空白", result.stderr)

        manifest = scope_baseline(valid_manifest())
        manifest["scope_candidates"][0]["seed_id"] = " SC1"
        reference_result = run_validator("scope", manifest)
        self.assertEqual(1, reference_result.returncode)
        self.assertIn("Review Briefにないseed", reference_result.stderr)

        path_scope = scope_baseline(valid_manifest())
        path_scope["scope_candidates"][0]["path_id"] = " P1"
        path_scope_result = run_validator("scope", path_scope)
        self.assertEqual(1, path_scope_result.returncode)
        self.assertIn("path_id: 前後空白", path_scope_result.stderr)

        path_discovery = discovery_baseline(valid_manifest())
        path_discovery["review_units"][0]["path_id"] = "P1 "
        path_discovery_result = run_validator("discovery", path_discovery)
        self.assertEqual(1, path_discovery_result.returncode)
        self.assertIn("path_id: 前後空白", path_discovery_result.stderr)

    def test_brief_identity_and_contracts_must_match_review_input(self) -> None:
        brief = valid_brief()
        brief["review_id"] = "different-review"
        brief["current_contracts"] = ["C1"]
        result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            brief=brief,
            review_input=valid_review_input(),
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("brief.review_id: Review Input", result.stderr)
        self.assertIn("brief.current_contracts: Review Input", result.stderr)

    def test_brief_revision_must_be_a_positive_integer(self) -> None:
        for revision in (0, -1, True, "1"):
            with self.subTest(revision=revision):
                brief = valid_brief()
                brief["revision"] = revision
                result = run_validator(
                    "scope", scope_baseline(valid_manifest()), brief=brief
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("正の整数", result.stderr)

    def test_condition_seeds_cover_each_review_input_condition_once(self) -> None:
        brief = valid_brief()
        duplicate = copy.deepcopy(brief["scope_seeds"][0])
        duplicate["id"] = "SC1-duplicate"
        duplicate["review_case_ids"] = ["C1-duplicate-case"]
        brief["scope_seeds"].append(duplicate)
        result = run_validator(
            "scope", scope_baseline(valid_manifest()), brief=brief
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("一度だけ被覆", result.stderr)

        missing = valid_brief()
        missing["scope_seeds"][0]["condition_id"] = "unknown-condition"
        missing_result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            brief=missing,
            review_input=valid_review_input(),
        )
        self.assertEqual(1, missing_result.returncode)
        self.assertIn("Review Inputにないcondition ID", missing_result.stderr)
        self.assertIn("C1 (0件)", missing_result.stderr)

    def test_non_condition_seed_cannot_claim_a_condition_id(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"][1]["condition_id"] = "C1"
        result = run_validator(
            "scope", scope_baseline(valid_manifest()), brief=brief
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("condition seed以外", result.stderr)

    def test_non_handoff_seed_cannot_claim_a_handoff_id(self) -> None:
        review_input = valid_review_input()
        review_input["scope_seeds"][0]["handoff_id"] = "H1"
        result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("handoff seed以外", result.stderr)

    def test_review_case_ids_are_globally_unique_across_seeds(self) -> None:
        brief = valid_brief()
        brief["scope_seeds"][1]["review_case_ids"] = ["C1-default"]
        result = run_validator(
            "scope", scope_baseline(valid_manifest()), brief=brief
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("全scope seedを通じて重複", result.stderr)

    def test_review_case_is_assigned_once_across_scope_and_review_units(self) -> None:
        scope = scope_baseline(valid_manifest())
        duplicate_scope = copy.deepcopy(scope["scope_candidates"][0])
        duplicate_scope["id"] = "S1-alternate"
        duplicate_scope["path_id"] = "P1-alternate"
        duplicate_scope["reachable_path"] = "alternate input -> output"
        scope["scope_candidates"].append(duplicate_scope)
        scoped = run_validator("scope", scope)
        self.assertEqual(1, scoped.returncode)
        self.assertIn("一度だけ割り当て", scoped.stderr)
        self.assertIn("複数のapplicable候補", scoped.stderr)

        discovery = discovery_baseline(valid_manifest())
        duplicate_unit = copy.deepcopy(discovery["review_units"][0])
        duplicate_unit["id"] = "R1-duplicate"
        discovery["review_units"].append(duplicate_unit)
        reviewed = run_validator("discovery", discovery)
        self.assertEqual(1, reviewed.returncode)
        self.assertIn("複数の確認単位", reviewed.stderr)

    def test_manifest_identity_and_revision_must_match_brief(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["review_id"] = "different-review"
        manifest["brief_revision"] = 9
        result = run_validator("scope", manifest)
        self.assertEqual(1, result.returncode)
        self.assertIn("manifest.review_id", result.stderr)
        self.assertIn("manifest.brief_revision", result.stderr)

    def test_manifest_revision_rejects_boolean_and_float_aliases(self) -> None:
        for revision in (True, 1.0):
            with self.subTest(revision=revision):
                manifest = scope_baseline(valid_manifest())
                manifest["brief_revision"] = revision
                result = run_validator("scope", manifest)
                self.assertEqual(1, result.returncode)
                self.assertIn("brief_revision: 正の整数", result.stderr)

    def test_revision_one_rejects_previous_brief_and_migrations(self) -> None:
        brief = valid_brief()
        brief["review_case_migrations"] = [
            {
                "previous_review_case_ids": ["C1-default"],
                "current_review_case_ids": ["C1-default"],
            }
        ]
        result = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            brief=brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("revision 1では指定できません", result.stderr)
        self.assertIn("revision 1ではキーと空配列[]", result.stderr)

    def test_revision_one_requires_migration_key_and_null_previous_digest(self) -> None:
        brief = valid_brief()
        del brief["review_case_migrations"]
        missing_key = run_validator(
            "scope", scope_baseline(valid_manifest()), brief=brief
        )
        self.assertEqual(1, missing_key.returncode)
        self.assertIn("キーと空配列[]", missing_key.stderr)

        missing_digest_input = valid_review_input()
        del missing_digest_input["previous_brief_digest"]
        missing_digest = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=missing_digest_input,
        )
        self.assertEqual(1, missing_digest.returncode)
        self.assertIn("previous_brief_digest: キー", missing_digest.stderr)

        review_input = valid_review_input()
        review_input["previous_brief_digest"] = "sha256:" + "0" * 64
        non_null = run_validator(
            "scope",
            scope_baseline(valid_manifest()),
            review_input=review_input,
        )
        self.assertEqual(1, non_null.returncode)
        self.assertIn("revision 1ではnull", non_null.stderr)

    def test_revision_after_one_requires_immediately_previous_brief(self) -> None:
        brief = valid_revised_brief()
        for stage in ("scope", "discovery", "candidate"):
            with self.subTest(stage=stage):
                source = valid_manifest()
                source["brief_revision"] = 2
                manifest = scope_baseline(source) if stage == "scope" else source
                if stage == "discovery":
                    manifest = discovery_baseline(source)
                missing = run_validator(stage, manifest, brief=brief)
                self.assertEqual(1, missing.returncode)
                self.assertIn("--previous-brief", missing.stderr)

        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2

        wrong_previous = valid_brief()
        wrong_previous["revision"] = 2
        wrong = run_validator(
            "scope",
            manifest,
            brief=brief,
            previous_brief=wrong_previous,
        )
        self.assertEqual(1, wrong.returncode)
        self.assertIn("直前revision", wrong.stderr)

        different_review = valid_brief()
        different_review["review_id"] = "different-review"
        mismatch = run_validator(
            "scope",
            manifest,
            brief=brief,
            previous_brief=different_review,
        )
        self.assertEqual(1, mismatch.returncode)
        self.assertIn("現Briefと一致", mismatch.stderr)

    def test_revision_two_accepts_complete_unchanged_case_migration_without_reason(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2
        result = run_validator(
            "scope",
            manifest,
            brief=valid_revised_brief(),
            previous_brief=valid_brief(),
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            f"brief_digest={canonical_digest(valid_revised_brief())}",
            result.stdout,
        )

    def test_previous_brief_digest_binds_the_exact_artifact(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2
        brief = valid_revised_brief()
        review_input = review_input_for_brief(
            brief, previous_brief=valid_brief()
        )
        substituted_previous = valid_brief()
        substituted_previous["target"] = "different artifact with same identity"
        mismatch = run_validator(
            "scope",
            manifest,
            review_input=review_input,
            brief=brief,
            previous_brief=substituted_previous,
        )
        self.assertEqual(1, mismatch.returncode)
        self.assertIn("実際に渡した直前Brief", mismatch.stderr)

        review_input["previous_brief_digest"] = "SHA256:not-a-digest"
        malformed = run_validator(
            "scope",
            manifest,
            review_input=review_input,
            brief=brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, malformed.returncode)
        self.assertIn("64桁の小文字16進数", malformed.stderr)

    def test_previous_brief_revision_shape_is_checked(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2
        previous_v1 = valid_brief()
        del previous_v1["review_case_migrations"]
        v1_result = run_validator(
            "scope",
            manifest,
            brief=valid_revised_brief(),
            previous_brief=previous_v1,
        )
        self.assertEqual(1, v1_result.returncode)
        self.assertIn("previous Brief", v1_result.stderr)
        self.assertIn("キーと空配列[]", v1_result.stderr)

        previous_v2 = valid_revised_brief()
        del previous_v2["review_case_migrations"]
        current_v3 = valid_revised_brief()
        current_v3["revision"] = 3
        current_manifest = copy.deepcopy(manifest)
        current_manifest["brief_revision"] = 3
        v2_result = run_validator(
            "scope",
            current_manifest,
            brief=current_v3,
            previous_brief=previous_v2,
        )
        self.assertEqual(1, v2_result.returncode)
        self.assertIn("revision 2以降では配列", v2_result.stderr)

    def test_case_migration_rejects_unknown_duplicate_empty_and_missing_rows(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2
        cases = (
            (
                [
                    {
                        "previous_review_case_ids": ["unknown"],
                        "current_review_case_ids": ["C1-default"],
                        "reason": "rename",
                    },
                    {
                        "previous_review_case_ids": ["H1-snapshot"],
                        "current_review_case_ids": ["H1-snapshot"],
                    },
                ],
                "直前Briefにないcase",
            ),
            (
                [
                    {
                        "previous_review_case_ids": ["C1-default", "C1-default"],
                        "current_review_case_ids": ["C1-default"],
                        "reason": "duplicate",
                    },
                    {
                        "previous_review_case_ids": ["H1-snapshot"],
                        "current_review_case_ids": ["H1-snapshot"],
                    },
                ],
                "previous_review_case_ids: 重複",
            ),
            (
                [
                    {
                        "previous_review_case_ids": [],
                        "current_review_case_ids": [],
                    },
                    {
                        "previous_review_case_ids": ["C1-default"],
                        "current_review_case_ids": ["C1-default"],
                    },
                    {
                        "previous_review_case_ids": ["H1-snapshot"],
                        "current_review_case_ids": ["H1-snapshot"],
                    },
                ],
                "両方を空",
            ),
            (
                [
                    {
                        "previous_review_case_ids": ["C1-default"],
                        "current_review_case_ids": ["C1-default"],
                    }
                ],
                "H1-snapshot (0件)",
            ),
        )
        for migrations, expected in cases:
            with self.subTest(expected=expected):
                brief = valid_revised_brief()
                brief["review_case_migrations"] = migrations
                result = run_validator(
                    "scope",
                    manifest,
                    brief=brief,
                    previous_brief=valid_brief(),
                )
                self.assertEqual(1, result.returncode)
                self.assertIn(expected, result.stderr)

    def test_case_rename_split_add_and_retire_require_reasons(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2

        renamed = valid_revised_brief()
        renamed["scope_seeds"][0]["review_case_ids"] = ["C1-renamed"]
        renamed["review_case_migrations"] = [
            {
                "previous_review_case_ids": ["C1-default"],
                "current_review_case_ids": ["C1-renamed"],
            },
            {
                "previous_review_case_ids": ["H1-snapshot"],
                "current_review_case_ids": ["H1-snapshot"],
            },
        ]
        renamed_manifest = copy.deepcopy(manifest)
        renamed_manifest["scope_candidates"][0]["review_case_ids"] = ["C1-renamed"]
        renamed_result = run_validator(
            "scope",
            renamed_manifest,
            brief=renamed,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, renamed_result.returncode)
        self.assertIn("reason", renamed_result.stderr)
        self.assertIn("current Brief migration:", renamed_result.stderr)
        renamed["review_case_migrations"][0]["reason"] = "case renamed"
        renamed_passed = run_validator(
            "scope",
            renamed_manifest,
            brief=renamed,
            previous_brief=valid_brief(),
        )
        self.assertEqual(0, renamed_passed.returncode, renamed_passed.stderr)

        split = valid_revised_brief()
        split["scope_seeds"][0]["review_case_ids"] = ["C1-a", "C1-b"]
        split["review_case_migrations"] = [
            {
                "previous_review_case_ids": ["C1-default"],
                "current_review_case_ids": ["C1-a", "C1-b"],
            },
            {
                "previous_review_case_ids": ["H1-snapshot"],
                "current_review_case_ids": ["H1-snapshot"],
            },
        ]
        split_manifest = copy.deepcopy(manifest)
        split_manifest["scope_candidates"][0]["review_case_ids"] = [
            "C1-a",
            "C1-b",
        ]
        split_result = run_validator(
            "scope",
            split_manifest,
            brief=split,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, split_result.returncode)
        self.assertIn("reason", split_result.stderr)

        previous_for_merge = valid_brief()
        previous_for_merge["scope_seeds"][0]["review_case_ids"] = [
            "C1-a",
            "C1-b",
        ]
        merged = valid_revised_brief()
        merged["review_case_migrations"] = [
            {
                "previous_review_case_ids": ["C1-a", "C1-b"],
                "current_review_case_ids": ["C1-default"],
            },
            {
                "previous_review_case_ids": ["H1-snapshot"],
                "current_review_case_ids": ["H1-snapshot"],
            },
        ]
        merge_result = run_validator(
            "scope",
            manifest,
            brief=merged,
            previous_brief=previous_for_merge,
        )
        self.assertEqual(1, merge_result.returncode)
        self.assertIn("reason", merge_result.stderr)

        added = valid_revised_brief()
        added["scope_seeds"][0]["review_case_ids"].append("C1-added")
        added["review_case_migrations"].append(
            {
                "previous_review_case_ids": [],
                "current_review_case_ids": ["C1-added"],
            }
        )
        added_manifest = copy.deepcopy(manifest)
        added_manifest["scope_candidates"][0]["review_case_ids"].append(
            "C1-added"
        )
        added_result = run_validator(
            "scope",
            added_manifest,
            brief=added,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, added_result.returncode)
        self.assertIn("reason", added_result.stderr)

        previous_with_retired = valid_brief()
        previous_with_retired["scope_seeds"][0]["review_case_ids"].append(
            "C1-retired"
        )
        retired = valid_revised_brief()
        retired["review_case_migrations"].append(
            {
                "previous_review_case_ids": ["C1-retired"],
                "current_review_case_ids": [],
            }
        )
        retired_result = run_validator(
            "scope",
            manifest,
            brief=retired,
            previous_brief=previous_with_retired,
        )
        self.assertEqual(1, retired_result.returncode)
        self.assertIn("reason", retired_result.stderr)

    def test_unchanged_case_with_a_different_owner_requires_reason(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2
        brief = valid_revised_brief()
        brief["scope_seeds"][0]["id"] = "SC1-new-owner"
        manifest["scope_candidates"][0]["seed_id"] = "SC1-new-owner"
        result = run_validator(
            "scope",
            manifest,
            brief=brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("reason", result.stderr)

        brief["review_case_migrations"][0]["reason"] = "seed owner changed"
        passed = run_validator(
            "scope",
            manifest,
            brief=brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(0, passed.returncode, passed.stderr)

    def test_condition_or_contract_owner_change_requires_reason(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2

        condition_input = valid_review_input()
        condition_input["condition_ids"] = ["C2"]
        condition_brief = valid_revised_brief()
        condition_brief["scope_seeds"][0]["condition_id"] = "C2"
        condition_result = run_validator(
            "scope",
            manifest,
            review_input=condition_input,
            brief=condition_brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, condition_result.returncode)
        self.assertIn("reason", condition_result.stderr)

        contract_brief = valid_revised_brief()
        contract_brief["handoffs"][0]["contract"] = "C1"
        contract_brief["scope_seeds"][0]["contract"] = "rendered output"
        contract_brief["scope_seeds"][1]["contract"] = "C1"
        contract_manifest = copy.deepcopy(manifest)
        contract_manifest["scope_candidates"][0]["contract"] = "rendered output"
        contract_manifest["scope_candidates"][1]["contract"] = "C1"
        contract_manifest["scope_candidates"][2]["handoff_contract"] = "C1"
        contract_result = run_validator(
            "scope",
            contract_manifest,
            brief=contract_brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, contract_result.returncode)
        self.assertIn("reason", contract_result.stderr)

    def test_seed_semantics_or_handoff_owner_change_requires_reason(self) -> None:
        manifest = scope_baseline(valid_manifest())
        manifest["brief_revision"] = 2

        source_brief = valid_revised_brief()
        source_brief["scope_seeds"][0]["source"] = "changed condition source"
        source_result = run_validator(
            "scope",
            manifest,
            brief=source_brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, source_result.returncode)
        self.assertIn("reason", source_result.stderr)
        source_brief["review_case_migrations"][0]["reason"] = (
            "condition source changed"
        )
        source_passed = run_validator(
            "scope",
            manifest,
            brief=source_brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(0, source_passed.returncode, source_passed.stderr)

        handoff_brief = valid_revised_brief()
        handoff_brief["handoffs"][0]["owner"] = "new integration owner"
        handoff_manifest = copy.deepcopy(manifest)
        handoff_manifest["scope_candidates"][2]["owner"] = (
            "new integration owner"
        )
        handoff_result = run_validator(
            "scope",
            handoff_manifest,
            brief=handoff_brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(1, handoff_result.returncode)
        self.assertIn("reason", handoff_result.stderr)
        handoff_brief["review_case_migrations"][1]["reason"] = (
            "handoff owner changed"
        )
        handoff_passed = run_validator(
            "scope",
            handoff_manifest,
            brief=handoff_brief,
            previous_brief=valid_brief(),
        )
        self.assertEqual(0, handoff_passed.returncode, handoff_passed.stderr)

    def test_previous_scope_baseline_cannot_cross_brief_revision(self) -> None:
        previous_scope = scope_baseline(valid_manifest())
        current_scope = copy.deepcopy(previous_scope)
        current_scope["brief_revision"] = 2
        result = run_validator(
            "scope",
            current_scope,
            brief=valid_revised_brief(),
            previous_brief=valid_brief(),
            previous_scope=previous_scope,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("brief_revision", result.stderr)

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
        brief = valid_brief()
        brief["scope_seeds"].append(
            {
                "id": "SCX",
                "kind": "changed-surface",
                "source": "changed adapter",
                "contract": "C1",
                "coverage_obligation": "classify-only",
                "review_case_ids": ["C1-alternate-path"],
            }
        )
        review_input = review_input_for_brief(brief)
        initial = scope_baseline(valid_manifest())
        initial["scope_candidates"].append(
            {
                "id": "SX0",
                "seed_id": "SCX",
                "classification": "not-applicable",
                "reason": "alternate path is not known yet",
                "boundary": "adapter boundary",
            }
        )
        updated = copy.deepcopy(initial)
        updated["scope_candidates"].append(
            {
                "id": "SX",
                "seed_id": "SCX",
                "classification": "applicable",
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "path_id": "PX",
                "boundary": "public output",
                "review_case_ids": ["C1-alternate-path"],
                "added_during_discovery": True,
                "addition_reason": "found while exploring",
            }
        )
        scoped = run_validator(
            "scope",
            updated,
            brief=brief,
            review_input=review_input,
            previous_scope=initial,
        )
        self.assertEqual(0, scoped.returncode, scoped.stderr)

        discovery = discovery_baseline(valid_manifest())
        discovery["scope_candidates"] = copy.deepcopy(updated["scope_candidates"])
        missing = run_validator(
            "discovery",
            discovery,
            brief=brief,
            review_input=review_input,
            baseline=updated,
        )
        self.assertEqual(1, missing.returncode)
        self.assertIn("SX", missing.stderr)

        discovery["review_units"].append(
            {
                "id": "RX",
                "scope_candidate_ids": ["SX"],
                "contract": "C1",
                "reachable_path": "alternate input -> output",
                "path_id": "PX",
                "review_case_id": "C1-alternate-path",
                "boundary": "public output",
                "status": "satisfied",
                "evidence_mode": "static",
                "evidence": "alternate caller and output",
                "guarantee": "C1 holds on the new path",
                "reviewer_id": "reviewer-1",
            }
        )
        passed = run_validator(
            "discovery",
            discovery,
            brief=brief,
            review_input=review_input,
            baseline=updated,
        )
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
        for field, padded_value in (
            ("origin_review_unit_id", " RX "),
            ("origin_review_case_id", " X-adapter "),
            ("reviewer_id", " reviewer-1 "),
        ):
            with self.subTest(tombstone_field=field):
                padded_baseline = copy.deepcopy(baseline)
                padded_manifest = copy.deepcopy(manifest)
                padded_baseline["scope_tombstones"][0][field] = padded_value
                padded_manifest["scope_tombstones"][0][field] = padded_value
                padded_discovery = discovery_baseline(padded_manifest)
                padded_result = run_validator(
                    "candidate",
                    padded_manifest,
                    brief=brief,
                    baseline=padded_baseline,
                    discovery=padded_discovery,
                )
                self.assertEqual(1, padded_result.returncode)
                self.assertIn(f"{field}: 前後空白", padded_result.stderr)
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
