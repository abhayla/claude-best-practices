"""Tests for fixture dependency versions and verdict-value schema.

Runtime verification (2026-04-22) caught two related defects:

- Bug 2: the hub fixture's package.json declared `@playwright/mcp@^0.1.0`,
  a version that doesn't exist on npm. The real latest is 0.0.70. Fresh
  `npm install` failed with `No matching version found`. Downstream
  projects copying this fixture hit the same error.

- Bug 12: the e2e-conductor-agent emitted `result: "BASELINES_UPDATED"`
  for `--update-baselines` runs, but the documented verdict schema lists
  only PASSED / NEEDS_REVIEW / FAILED. Downstream stage-gate aggregators
  parsing `result` for pass/fail would hit an unknown value.

These tests pin both invariants as property assertions:
  - package.json MUST resolve @playwright/mcp to a real npm version range
  - pipeline_aggregator.py MUST treat BASELINES_UPDATED as a non-failing
    result (equivalent to PASSED for gate purposes)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PKG_JSON = (
    REPO_ROOT / "scripts" / "tests" / "fixtures" / "playwright-demo" / "package.json"
)


@pytest.fixture(scope="module")
def package_json() -> dict:
    assert FIXTURE_PKG_JSON.is_file(), f"fixture missing: {FIXTURE_PKG_JSON}"
    with FIXTURE_PKG_JSON.open(encoding="utf-8") as f:
        return json.load(f)


class TestFixtureMcpVersion:
    """Bug 2 regression: @playwright/mcp version must resolve on npm."""

    def test_playwright_mcp_version_is_not_hallucinated(self, package_json):
        """Version 0.1.0 does not exist on npm; the real series is 0.0.x.
        Pin against the specific bad range we introduced."""
        dev = package_json.get("devDependencies", {})
        spec = dev.get("@playwright/mcp")
        assert spec is not None, "@playwright/mcp must be declared"
        assert spec != "^0.1.0", (
            "@playwright/mcp@^0.1.0 is a hallucinated version — no such "
            "release exists on npm. Use ^0.0.70 (or the current latest "
            "stable in the 0.0.x series)."
        )

    def test_playwright_mcp_version_shape_is_valid(self, package_json):
        """Accept any semver range prefix (^, ~, >=, or exact) resolving to
        a 0.0.x or 1.x.x version — the real series."""
        spec = package_json["devDependencies"]["@playwright/mcp"]
        # Accept: ^0.0.70, ~0.0.70, >=0.0.70, 0.0.70, *, or later majors
        valid = re.match(r"^[\^~>=<* ]*(\d+)\.(\d+)\.(\d+)", spec)
        assert valid, f"@playwright/mcp spec '{spec}' is not a valid semver range"
        major, minor, patch = (int(valid.group(i)) for i in (1, 2, 3))
        # As of runtime verification (2026-04-22), latest is 0.0.70.
        # Anything in 0.0.x >= 70, or 0.x.x >= 1, or 1.x.x is acceptable.
        assert (major, minor, patch) >= (0, 0, 70) or (major, minor) >= (0, 1), (
            f"@playwright/mcp version '{spec}' is earlier than 0.0.70 — "
            "may not exist on npm or missing recent features."
        )


class TestBaselinesUpdatedVerdict:
    """Bug 12 regression: BASELINES_UPDATED verdict must be recognized
    by the standalone aggregator (scripts/pipeline_aggregator.py).

    The aggregator treats any `result` not in the pass-set as a
    potential failure. BASELINES_UPDATED is a legitimate non-failure
    outcome (baseline-update mode deliberately skips verification), so
    it must be added to the pass-set."""

    def test_aggregator_treats_baselines_updated_as_pass(self, tmp_path: Path):
        from scripts.pipeline_aggregator import aggregate, EXIT_PASSED

        results = tmp_path / "test-results"
        results.mkdir(parents=True, exist_ok=True)
        (results / "e2e-pipeline.json").write_text(
            json.dumps({
                "skill": "e2e-conductor-agent",
                "result": "BASELINES_UPDATED",
                "schema_version": "1.0.0",
                "timestamp": "2026-04-22T00:00:00Z",
                "summary": {
                    "total": 7,
                    "passed": 6,
                    "failed": 1,
                    "healed": 0,
                    "expected_changes": 0,
                    "known_issues": 0,
                    "note": "Baseline-update mode — failures do not block.",
                },
                "failures": [],
            }),
            encoding="utf-8",
        )
        (results / "fix-loop.json").write_text(
            json.dumps({"skill": "fix-loop", "result": "PASSED"}),
            encoding="utf-8",
        )

        exit_code, verdict = aggregate(
            results_dir=results, strict_contradictions=False, run_id="t1"
        )

        assert exit_code == EXIT_PASSED, (
            f"BASELINES_UPDATED must map to PASSED exit code, got {exit_code}. "
            f"Verdict: {verdict.get('result')}. The aggregator's pass-set "
            "must recognize BASELINES_UPDATED as a non-failing outcome."
        )
        assert verdict["result"] == "PASSED", (
            "aggregator unified verdict should be PASSED when all stages are "
            f"pass-set (including BASELINES_UPDATED); got {verdict['result']!r}"
        )


class TestConductorAgentDocumentsBaselinesUpdatedVerdict:
    """Ensure the e2e-conductor-agent.md body documents BASELINES_UPDATED
    as one of the verdict outcomes, so downstream consumers know it can
    appear in state files."""

    def test_conductor_agent_lists_baselines_updated(self):
        agent_path = (
            REPO_ROOT / "core" / ".claude" / "agents" / "e2e-conductor-agent.md"
        )
        content = agent_path.read_text(encoding="utf-8")
        assert "BASELINES_UPDATED" in content, (
            "e2e-conductor-agent.md must document BASELINES_UPDATED in its "
            "verdict schema — runtime verification (2026-04-22) confirmed "
            "the agent emits this value for --update-baselines runs."
        )
