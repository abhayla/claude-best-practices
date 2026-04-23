"""Tests for deterministic-regex classification rules in e2e-pipeline.yml.

These rules are read by test-failure-analyzer-agent at runtime to bypass the
LLM classifier for clear-cut failures. The patterns MUST match the actual
error strings Playwright produces, and the rule ORDER matters (first-match
wins) — specific rules must come before generic ones.

Verified against real Playwright 1.49+ output captured from the
v2-pipeline-testbed runtime verification run (2026-04-23).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "core" / ".claude" / "config" / "e2e-pipeline.yml"


@pytest.fixture(scope="module")
def rules() -> list[dict]:
    """Load classification_rules from the canonical config file."""
    with CONFIG_PATH.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    rules = cfg.get("classification_rules", [])
    assert rules, "classification_rules missing from e2e-pipeline.yml"
    return rules


def _first_match(rules: list[dict], text: str) -> dict | None:
    """Apply rules first-match-wins, returning the winning rule or None."""
    for rule in rules:
        flags = re.IGNORECASE if rule.get("flags") == "i" else 0
        if re.search(rule["pattern"], text, flags):
            return rule
    return None


# ── Real Playwright error strings captured from runtime verification ──────


# From v2-pipeline-testbed scenario=broken-locator, 2026-04-22:
# tests/dashboard.spec.ts tried getByRole('button', { name: 'Refresh' })
# but server swapped the label to 'Reload Users'.
REAL_PLAYWRIGHT_LOCATOR_FAILURE = (
    "TimeoutError: locator.click: Timeout 5000ms exceeded.\n"
    "Call log:\n"
    "  - waiting for getByRole('button', { name: 'Refresh' })\n"
)

REAL_PLAYWRIGHT_LOCATOR_FAILURE_BY_LABEL = (
    "TimeoutError: locator.fill: Timeout 5000ms exceeded.\n"
    "Call log:\n"
    "  - waiting for getByLabel('Email')\n"
)

REAL_PLAYWRIGHT_LOCATOR_FAILURE_BY_TEST_ID = (
    "TimeoutError: locator.click: Timeout 5000ms exceeded.\n"
    "Call log:\n"
    "  - waiting for getByTestId('submit-btn')\n"
)

# From v2-pipeline-testbed scenario=visual-change, 2026-04-22:
# CSS color shift caused 1769-pixel baseline drift.
REAL_PLAYWRIGHT_SCREENSHOT_DIFF = (
    "Error: expect(locator).toHaveScreenshot(expected) failed\n\n"
    "  1769 pixels (ratio 0.06 of all image pixels) are different.\n\n"
    "Expected: D:\\path\\tests\\visual.spec.ts-snapshots\\dashboard-heading-chromium-win32.png\n"
    "Received: D:\\path\\test-evidence\\latest\\visual-dashboard-heading-actual.png\n"
    "  Diff: dashboard-heading-diff.png\n\n"
    "Snapshot: dashboard-heading.png\n"
)

# A pure timeout with no locator context (e.g., page.goto timed out) —
# this SHOULD be classified as TIMEOUT, not SELECTOR.
REAL_PLAYWRIGHT_PURE_TIMEOUT = (
    "TimeoutError: page.goto: Timeout 30000ms exceeded.\n"
    "Call log:\n"
    "  - navigating to \"http://localhost:4317/\"\n"
)

# Upstream unavailable — INFRASTRUCTURE classification.
REAL_PLAYWRIGHT_503_ERROR = (
    "Error: expect(received).toHaveCount(expected)\n"
    "\n"
    "503 Service Unavailable\n"
    "upstream unavailable\n"
)

# Network-layer failure.
REAL_CONNECTION_REFUSED = (
    "Error: getaddrinfo ENOTFOUND localhost:4317\n"
    "connect ECONNREFUSED 127.0.0.1:4317\n"
)

# SQL schema drift.
REAL_SQL_MIGRATION_FAILURE = (
    'sqlalchemy.exc.OperationalError: (psycopg2.errors.UndefinedTable) '
    'relation "users" does not exist\n'
    'LINE 1: SELECT * FROM users\n'
)


# ── Tests: each rule must fire on the real string we saw at runtime ──────


class TestPlaywrightLocatorFailureRule:
    """playwright_locator_failure MUST fire on real Playwright locator
    errors — the original v2.0.0 pattern required a `Locator:` header
    that Playwright does not emit. Runtime verification (2026-04-22)
    confirmed every SELECTOR failure was misclassified as TIMEOUT."""

    def test_matches_real_getByRole_failure(self, rules):
        match = _first_match(rules, REAL_PLAYWRIGHT_LOCATOR_FAILURE)
        assert match is not None, "no rule matched real getByRole failure"
        assert match["category"] == "SELECTOR", (
            f"expected SELECTOR for getByRole locator failure, got "
            f"{match['category']} via rule {match.get('id')}"
        )

    def test_matches_real_getByLabel_failure(self, rules):
        match = _first_match(rules, REAL_PLAYWRIGHT_LOCATOR_FAILURE_BY_LABEL)
        assert match is not None
        assert match["category"] == "SELECTOR"

    def test_matches_real_getByTestId_failure(self, rules):
        match = _first_match(rules, REAL_PLAYWRIGHT_LOCATOR_FAILURE_BY_TEST_ID)
        assert match is not None
        assert match["category"] == "SELECTOR"

    def test_fires_before_playwright_timeout_rule(self, rules):
        """Rule ORDER matters — locator_failure must come before timeout,
        otherwise `TimeoutError:` prefix wins and misclassifies SELECTOR."""
        loc_idx = next(
            (i for i, r in enumerate(rules) if r.get("id") == "playwright_locator_failure"),
            None,
        )
        timeout_idx = next(
            (i for i, r in enumerate(rules) if r.get("id") == "playwright_timeout"),
            None,
        )
        assert loc_idx is not None, "playwright_locator_failure rule missing"
        assert timeout_idx is not None, "playwright_timeout rule missing"
        assert loc_idx < timeout_idx, (
            f"playwright_locator_failure (at {loc_idx}) must come before "
            f"playwright_timeout (at {timeout_idx}) — first-match-wins"
        )


class TestPureTimeoutStillClassifiedAsTimeout:
    """A pure timeout without locator context (e.g., page.goto) must
    still classify as TIMEOUT, not SELECTOR. Relaxing the locator rule
    must not overreach."""

    def test_page_goto_timeout_is_timeout(self, rules):
        match = _first_match(rules, REAL_PLAYWRIGHT_PURE_TIMEOUT)
        assert match is not None
        assert match["category"] == "TIMEOUT", (
            f"page.goto timeout should be TIMEOUT, got "
            f"{match['category']} via rule {match.get('id')}"
        )


class TestScreenshotBaselineDiffRule:
    """screenshot_baseline_diff MUST match real Playwright visual-diff output.
    The v2.0.0 pattern required `Screenshot (differs from baseline|
    comparison failed)` which Playwright doesn't emit — actual format is
    `toHaveScreenshot ... failed ... N pixels are different`."""

    def test_matches_real_pixel_diff(self, rules):
        match = _first_match(rules, REAL_PLAYWRIGHT_SCREENSHOT_DIFF)
        assert match is not None, "no rule matched real screenshot diff"
        assert match["category"] == "VISUAL_REGRESSION", (
            f"expected VISUAL_REGRESSION for toHaveScreenshot diff, got "
            f"{match['category']} via rule {match.get('id')}"
        )


class TestInfrastructureRules:
    """Infrastructure-class errors (503, ECONNREFUSED) must fire the
    INFRASTRUCTURE rules, and must come before generic timeout/assertion
    rules so they win first-match-wins."""

    def test_503_is_infrastructure(self, rules):
        match = _first_match(rules, REAL_PLAYWRIGHT_503_ERROR)
        assert match is not None
        assert match["category"] == "INFRASTRUCTURE"

    def test_connection_refused_is_infrastructure(self, rules):
        match = _first_match(rules, REAL_CONNECTION_REFUSED)
        assert match is not None
        assert match["category"] == "INFRASTRUCTURE"

    def test_sql_migration_failure(self, rules):
        match = _first_match(rules, REAL_SQL_MIGRATION_FAILURE)
        assert match is not None
        assert match["category"] == "MIGRATION_FAILURE"


class TestRuleSchemaInvariants:
    """Structural invariants every rule must satisfy."""

    def test_every_rule_has_required_fields(self, rules):
        required = {"id", "pattern", "category", "confidence"}
        for rule in rules:
            missing = required - rule.keys()
            assert not missing, (
                f"rule {rule.get('id', '<unnamed>')} missing: {missing}"
            )

    def test_every_rule_id_is_unique(self, rules):
        ids = [r["id"] for r in rules]
        duplicates = {rid for rid in ids if ids.count(rid) > 1}
        assert not duplicates, f"duplicate rule ids: {duplicates}"

    def test_confidence_values_are_calibrated(self, rules):
        """Deterministic-regex matches should be high-confidence (>= 0.85)
        per the test-failure-analyzer-agent v2.0.0 NON-NEGOTIABLE rules."""
        for rule in rules:
            c = rule["confidence"]
            assert 0.85 <= c <= 1.0, (
                f"rule {rule['id']} confidence {c} outside [0.85, 1.0] — "
                "deterministic regex matches should be high-confidence"
            )

    def test_every_pattern_is_valid_regex(self, rules):
        for rule in rules:
            try:
                re.compile(rule["pattern"])
            except re.error as e:
                pytest.fail(
                    f"rule {rule['id']} has invalid regex pattern: {e}"
                )
