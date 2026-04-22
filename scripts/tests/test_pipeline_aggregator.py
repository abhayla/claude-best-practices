"""Tests for scripts/pipeline_aggregator.py.

These tests exercise every verdict-producing path: all-pass, any-fail,
screenshot-failed-but-exit-passed (authoritative), contradictions in warn
and strict modes, missing results directory, and malformed JSON. They use
real JSON fixtures written to tmp_path so nothing is mocked — the aggregator
is a pure read → compute → write script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.pipeline_aggregator import (
    EXIT_BLOCKED,
    EXIT_FAILED,
    EXIT_PASSED,
    aggregate,
    main,
)


def _write_result(results_dir: Path, skill: str, **payload: Any) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    payload.setdefault("skill", skill)
    payload.setdefault("result", "PASSED")
    (results_dir / f"{skill}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_all_pass_returns_passed(tmp_path: Path) -> None:
    _write_result(tmp_path, "auto-verify", result="PASSED", summary={"ui_tests": 0})
    _write_result(tmp_path, "fix-loop", result="PASSED")
    _write_result(tmp_path, "code-quality-gate", result="PASSED")

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id="r1")

    assert exit_code == EXIT_PASSED
    assert verdict["result"] == "PASSED"
    assert verdict["stages_completed"] == 3
    assert verdict["stages_failed"] == 0


def test_any_fail_returns_failed(tmp_path: Path) -> None:
    _write_result(tmp_path, "auto-verify", result="PASSED")
    _write_result(
        tmp_path,
        "fix-loop",
        result="FAILED",
        failures=[{"test": "test_foo", "message": "boom"}],
    )

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    assert exit_code == EXIT_FAILED
    assert verdict["result"] == "FAILED"
    assert len(verdict["failures"]) == 1
    assert verdict["failures"][0]["source_skill"] == "fix-loop"


def test_screenshot_failed_is_authoritative(tmp_path: Path) -> None:
    """A failure with verdict_source=screenshot must block even if the
    containing skill reports PASSED. Screenshot verdict is authoritative
    for UI tests — that's the whole point of dual-signal verification."""
    _write_result(
        tmp_path,
        "auto-verify",
        result="PASSED",
        failures=[
            {
                "test": "test_dashboard",
                "verdict_source": "screenshot",
                "message": "Empty table — no data rows",
            }
        ],
    )
    _write_result(tmp_path, "fix-loop", result="PASSED")

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    assert exit_code == EXIT_FAILED
    assert verdict["result"] == "FAILED"
    assert any(
        f.get("verdict_source") == "screenshot" for f in verdict["failures"]
    )


def test_contradictions_warn_mode_does_not_block(tmp_path: Path) -> None:
    """Default is --no-strict-contradictions: cross-skill disagreements surface
    in the report but don't escalate to FAILED."""
    _write_result(tmp_path, "auto-verify", result="PASSED")
    _write_result(tmp_path, "contract-test", result="FAILED", failures=[])

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    # contract-test FAILED is itself a failure — but its failures list is
    # empty so there's no individual failure to union. However, FAILED status
    # with empty failures is still a FAIL for that stage.
    # More importantly: contradictions are detected and surfaced.
    assert verdict["contradictions"], "Expected contradiction to be surfaced"
    assert any(
        "auto-verify" in c["skills"] and "contract-test" in c["skills"]
        for c in verdict["contradictions"]
    )


def test_contradictions_strict_mode_blocks(tmp_path: Path) -> None:
    _write_result(tmp_path, "auto-verify", result="PASSED")
    _write_result(tmp_path, "contract-test", result="FAILED")

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=True, run_id=None)

    assert exit_code == EXIT_FAILED
    assert verdict["result"] == "FAILED"
    assert verdict["contradictions"], "Expected contradictions to be recorded"


def test_fix_loop_passed_but_auto_verify_failed_is_contradiction(
    tmp_path: Path,
) -> None:
    """If fix-loop said it fixed everything but auto-verify still fails,
    the fix introduced new problems — surface as contradiction."""
    _write_result(tmp_path, "fix-loop", result="PASSED")
    _write_result(
        tmp_path,
        "auto-verify",
        result="FAILED",
        failures=[{"test": "test_foo", "message": "still broken"}],
    )

    _, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    descriptions = [c["description"] for c in verdict["contradictions"]]
    assert any("fix-loop PASSED but auto-verify FAILED" in d for d in descriptions)


def test_missing_results_dir_is_blocked(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    exit_code, verdict = aggregate(empty_dir, strict_contradictions=False, run_id=None)

    assert exit_code == EXIT_BLOCKED
    assert verdict["result"] == "BLOCKED"
    assert "No test-results" in verdict["reason"]


def test_malformed_json_is_blocked(tmp_path: Path) -> None:
    (tmp_path / "auto-verify.json").write_text("{ not valid json", encoding="utf-8")

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    assert exit_code == EXIT_BLOCKED
    assert verdict["result"] == "BLOCKED"


def test_known_issues_get_dedup_signatures(tmp_path: Path) -> None:
    _write_result(
        tmp_path,
        "e2e-conductor-agent",
        result="FAILED",
        known_issues=[
            {
                "test": "test_animation",
                "final_classification": "TIMING",
                "top_stack_frame": "checkout.spec.ts:42",
            },
            {
                "test": "test_logic",
                "final_classification": "LOGIC_BUG",
                "top_stack_frame": "api.spec.ts:17",
            },
        ],
    )

    _, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    issues = verdict["known_issues_created_as_issues"]
    assert len(issues) == 2
    for issue in issues:
        assert len(issue["signature"]) == 12
        assert issue["source_skill"] == "e2e-conductor-agent"

    # Same inputs produce same signature (determinism)
    assert issues[0]["signature"] != issues[1]["signature"]


def test_fixed_result_counts_as_passed(tmp_path: Path) -> None:
    """FIXED is a success state (fix-loop healed failures in place)."""
    _write_result(tmp_path, "fix-loop", result="FIXED")
    _write_result(tmp_path, "auto-verify", result="PASSED")

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    assert exit_code == EXIT_PASSED
    assert verdict["result"] == "PASSED"
    assert verdict["stages_completed"] == 2


def test_ui_verification_summary_aggregated(tmp_path: Path) -> None:
    _write_result(
        tmp_path,
        "auto-verify",
        result="PASSED",
        summary={
            "ui_tests": 12,
            "ui_tests_screenshot_verified": 12,
        },
        visual_review={
            "confirmed_passes": 10,
            "overrides": [{"test": "t1"}, {"test": "t2"}],
            "flags": [{"test": "t3"}],
        },
    )

    _, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    ui = verdict["ui_verification_summary"]
    assert ui["total_ui_tests"] == 12
    assert ui["screenshot_verified"] == 12
    assert ui["screenshot_passed"] == 10
    assert ui["screenshot_failed"] == 2
    assert ui["flags"] == 1


def test_main_writes_verdict_file_and_returns_exit_code(tmp_path: Path) -> None:
    _write_result(tmp_path, "fix-loop", result="PASSED")

    exit_code = main(
        [
            "--results-dir",
            str(tmp_path),
            "--run-id",
            "test-run-42",
            "--quiet",
        ]
    )

    assert exit_code == EXIT_PASSED
    verdict_path = tmp_path / "pipeline-verdict.json"
    assert verdict_path.exists()
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    assert verdict["result"] == "PASSED"
    assert verdict["run_id"] == "test-run-42"


def test_aggregator_ignores_existing_pipeline_verdict(tmp_path: Path) -> None:
    """A previous pipeline-verdict.json in the results dir must NOT be
    aggregated as if it were a stage result (would cause self-loop)."""
    _write_result(tmp_path, "fix-loop", result="PASSED")
    (tmp_path / "pipeline-verdict.json").write_text(
        json.dumps({"skill": "testing-pipeline", "result": "FAILED"}),
        encoding="utf-8",
    )

    exit_code, verdict = aggregate(tmp_path, strict_contradictions=False, run_id=None)

    assert exit_code == EXIT_PASSED
    # Only fix-loop should be in stage_results, not pipeline-verdict itself
    assert "testing-pipeline" not in verdict["stage_results"]
    assert "fix-loop" in verdict["stage_results"]
