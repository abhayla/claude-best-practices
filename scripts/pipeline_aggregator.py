"""Standalone aggregator for testing-pipeline results.

Reads every test-results/*.json file, applies the union-of-failures rule,
enforces screenshot-authoritative UI verdicts, detects cross-stage
contradictions, and writes test-results/pipeline-verdict.json.

This is the SINGLE source of truth for pipeline pass/fail. Individual skill
results are inputs; the aggregator's output is the only authoritative verdict.

The same logic is documented inline in
core/.claude/agents/testing-pipeline-master-agent.md so the T1 master agent
can run it during interactive pipeline runs. This script exists so CI can
run the same logic headlessly (without Claude Code).

Exit codes:
    0 - result PASSED
    1 - result FAILED (any skill failed, any screenshot verdict failed,
        or contradictions detected under --strict-contradictions)
    2 - result BLOCKED (no test-results/*.json found or a result file could
        not be parsed — missing upstream evidence)
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

RESULT_PASSED = "PASSED"
RESULT_FAILED = "FAILED"
RESULT_FIXED = "FIXED"
RESULT_BLOCKED = "BLOCKED"
RESULT_BASELINES_UPDATED = "BASELINES_UPDATED"
RESULT_NEEDS_REVIEW = "NEEDS_REVIEW"

EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2

# Results that count as non-failures for stage-gate purposes. BASELINES_UPDATED
# is emitted by e2e-conductor-agent for --update-baselines runs (which
# deliberately skip verification + healing per the v2 spec) and must be
# treated as a pass. NEEDS_REVIEW is emitted when expected_changes are
# detected (intentional UI drift awaiting human approval).
PASS_STATUSES = {
    RESULT_PASSED,
    RESULT_FIXED,
    RESULT_BASELINES_UPDATED,
    RESULT_NEEDS_REVIEW,
}


class Contradiction(TypedDict):
    description: str
    skills: list[str]


def _read_results(results_dir: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Read every *.json file in test-results/. Returns (results, error) where
    error is None on success or a human-readable message on parse failure."""
    paths = sorted(glob.glob(str(results_dir / "*.json")))
    if not paths:
        return [], "No test-results/*.json files found — cannot aggregate"

    results: list[dict[str, Any]] = []
    for path in paths:
        if Path(path).name == "pipeline-verdict.json":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            return [], f"Could not parse {path}: {exc}"
        if "result" not in payload:
            return [], f"{path} missing required 'result' field"
        results.append(payload)
    return results, None


def _collect_failures(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union of per-skill failures. Rules:

    - Every result reporting FAILED contributes all entries in its `failures` list.
    - Every result reporting PASSED contributes ONLY failures where
      `verdict_source == "screenshot"` — the screenshot verdict is authoritative
      for UI tests regardless of the enclosing skill's top-level verdict, so a
      PASSED skill with a screenshot-failed entry is still a failure we surface.
    - Results reporting FIXED are treated like PASSED for this purpose.
    """
    all_failures: list[dict[str, Any]] = []
    for result in results:
        skill_name = result.get("skill", "unknown")
        top_level = result.get("result")
        for failure in result.get("failures", []):
            if top_level == RESULT_FAILED or failure.get("verdict_source") == "screenshot":
                enriched = dict(failure)
                enriched["source_skill"] = skill_name
                all_failures.append(enriched)
    return all_failures


def _collect_screenshot_failures(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Screenshot verdict is authoritative for UI tests. Any failure with
    verdict_source=screenshot is ALWAYS blocking, no exceptions."""
    screenshot_failures: list[dict[str, Any]] = []
    for result in results:
        for failure in result.get("failures", []):
            if failure.get("verdict_source") == "screenshot":
                screenshot_failures.append(failure)
    return screenshot_failures


def _detect_contradictions(
    results: list[dict[str, Any]],
) -> list[Contradiction]:
    """Cross-skill disagreements on overlapping concerns.

    A contradiction is when one skill reports PASSED and a related skill
    reports FAILED — suggesting the first skill missed something its peer
    caught. These do not overlap with screenshot-verdict FAILED + exit-code
    PASSED (that's the designed behavior, not a contradiction).
    """
    statuses = {r.get("skill"): r.get("result") for r in results}
    contradictions: list[Contradiction] = []

    def passed(skill: str) -> bool:
        return statuses.get(skill) in PASS_STATUSES

    def failed(skill: str) -> bool:
        return statuses.get(skill) == RESULT_FAILED

    if passed("auto-verify") and failed("contract-test"):
        contradictions.append({
            "description": "auto-verify PASSED but contract-test FAILED — API compatibility issue",
            "skills": ["auto-verify", "contract-test"],
        })
    if passed("auto-verify") and failed("perf-test"):
        contradictions.append({
            "description": "auto-verify PASSED but perf-test FAILED — performance regression",
            "skills": ["auto-verify", "perf-test"],
        })
    if passed("fix-loop") and failed("auto-verify"):
        contradictions.append({
            "description": "fix-loop PASSED but auto-verify FAILED — fix introduced new failures",
            "skills": ["fix-loop", "auto-verify"],
        })
    return contradictions


def _summarize_ui_verification(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Extract UI verification summary from auto-verify and e2e results.
    These are the two sources that report ui_tests counts."""
    total_ui = 0
    screenshot_verified = 0
    screenshot_passed = 0
    screenshot_failed = 0
    flags = 0
    for result in results:
        skill = result.get("skill", "")
        if skill in ("auto-verify", "e2e-conductor-agent"):
            summary = result.get("summary", {})
            total_ui += summary.get("ui_tests", 0)
            verified = summary.get("ui_tests_screenshot_verified", 0)
            screenshot_verified += verified
            visual = result.get("visual_review", {})
            if isinstance(visual, dict):
                screenshot_passed += visual.get("confirmed_passes", 0)
                screenshot_failed += len(visual.get("overrides", []))
                flags += len(visual.get("flags", []))
    return {
        "total_ui_tests": total_ui,
        "screenshot_verified": screenshot_verified,
        "screenshot_passed": screenshot_passed,
        "screenshot_failed": screenshot_failed,
        "verdict_source": "screenshot" if total_ui else "none",
        "flags": flags,
    }


def _known_issues_signatures(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Pull known_issues out of each skill's result and attach the signature
    that testing-pipeline-master-agent uses for GitHub Issue dedup."""
    issues: list[dict[str, Any]] = []
    for result in results:
        for issue in result.get("known_issues", []):
            key = (
                f"{issue.get('test', '')}|"
                f"{issue.get('final_classification', '')}|"
                f"{issue.get('top_stack_frame', '')}"
            )
            signature = hashlib.sha256(key.encode()).hexdigest()[:12]
            enriched = dict(issue)
            enriched["signature"] = signature
            enriched["source_skill"] = result.get("skill", "unknown")
            issues.append(enriched)
    return issues


def aggregate(
    results_dir: Path,
    strict_contradictions: bool,
    run_id: str | None,
) -> tuple[int, dict[str, Any]]:
    """Compute the unified verdict from test-results/ and return
    (exit_code, verdict_dict). The caller is responsible for writing the
    verdict JSON and printing human-readable output."""
    results, read_err = _read_results(results_dir)
    if read_err is not None:
        verdict = {
            "pipeline": "testing-pipeline",
            "schema_version": "1.0.0",
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "result": RESULT_BLOCKED,
            "reason": read_err,
            "stages_completed": 0,
            "stages_failed": 0,
            "stage_results": {},
            "failures": [],
            "contradictions": [],
            "known_issues_created_as_issues": [],
        }
        return EXIT_BLOCKED, verdict

    failures = _collect_failures(results)
    screenshot_failures = _collect_screenshot_failures(results)
    contradictions = _detect_contradictions(results)

    stage_results = {r.get("skill", "unknown"): r.get("result") for r in results}
    stages_completed = sum(1 for r in results if r.get("result") in PASS_STATUSES)
    stages_failed = sum(1 for r in results if r.get("result") == RESULT_FAILED)

    # Any stage reporting FAILED fails the pipeline, even when the stage
    # provided an empty failures[] array (e.g., a skill that moved a test
    # to known_issues without an individual failure entry). The "union of
    # failures" rule is a superset — stage-level FAILED counts.
    any_stage_failed = stages_failed > 0

    if failures or screenshot_failures or any_stage_failed:
        result = RESULT_FAILED
        exit_code = EXIT_FAILED
    elif contradictions and strict_contradictions:
        result = RESULT_FAILED
        exit_code = EXIT_FAILED
    else:
        result = RESULT_PASSED
        exit_code = EXIT_PASSED

    verdict = {
        "pipeline": "testing-pipeline",
        "schema_version": "1.0.0",
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result": result,
        "stages_completed": stages_completed,
        "stages_failed": stages_failed,
        "stage_results": stage_results,
        "ui_verification_summary": _summarize_ui_verification(results),
        "failures": failures,
        "contradictions": contradictions,
        "known_issues_created_as_issues": _known_issues_signatures(results),
    }
    return exit_code, verdict


def _print_summary(verdict: dict[str, Any]) -> None:
    """Human-readable summary for CI logs."""
    print(f"Pipeline Verdict: {verdict['result']}")
    print(f"  Run ID: {verdict.get('run_id') or 'none'}")
    print(
        f"  Stages: {verdict['stages_completed']} passed, "
        f"{verdict['stages_failed']} failed"
    )
    stage_results = verdict.get("stage_results", {})
    if stage_results:
        print("  Stage results:")
        for skill, status in sorted(stage_results.items()):
            print(f"    {skill}: {status}")
    ui = verdict.get("ui_verification_summary", {})
    if ui and ui.get("total_ui_tests"):
        print(
            f"  UI: {ui['total_ui_tests']} tests, "
            f"{ui['screenshot_verified']} screenshot-verified, "
            f"{ui['screenshot_failed']} overrides"
        )
    failures = verdict.get("failures", [])
    if failures:
        print(f"  Failures ({len(failures)}):")
        for failure in failures[:20]:
            source = failure.get("source_skill", "?")
            test = failure.get("test", "unknown")
            message = failure.get("message", "no message")
            print(f"    [{source}] {test}: {message}")
        if len(failures) > 20:
            print(f"    ... and {len(failures) - 20} more")
    contradictions = verdict.get("contradictions", [])
    if contradictions:
        print(f"  Contradictions ({len(contradictions)}):")
        for item in contradictions:
            print(f"    {item['description']}")
    issues = verdict.get("known_issues_created_as_issues", [])
    if issues:
        print(f"  Known issues: {len(issues)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate test-results/*.json into pipeline-verdict.json",
    )
    parser.add_argument(
        "--results-dir",
        default="test-results",
        help="Directory containing *.json stage results (default: test-results)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Pipeline run ID to record in the verdict (optional)",
    )
    parser.add_argument(
        "--strict-contradictions",
        action="store_true",
        help="Escalate contradictions to FAILED (default: warn only)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write the verdict JSON (default: {results_dir}/pipeline-verdict.json)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Skip human-readable summary output",
    )
    args = parser.parse_args(argv)

    results_dir = Path(args.results_dir)
    exit_code, verdict = aggregate(
        results_dir=results_dir,
        strict_contradictions=args.strict_contradictions,
        run_id=args.run_id,
    )

    output_path = Path(args.output) if args.output else results_dir / "pipeline-verdict.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2)

    if not args.quiet:
        _print_summary(verdict)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
