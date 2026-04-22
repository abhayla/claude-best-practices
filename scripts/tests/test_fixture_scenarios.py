"""Tests for the playwright-demo fixture's DEMO_SCENARIO handlers.

Runtime verification (2026-04-22) revealed two fixture-design bugs: the
`timing` scenario's 3000ms server delay was within Playwright's default
5000ms expect auto-retry window (so tests passed when they should fail),
and the `flaky` scenario's counter-based logic (`counter % 2 === 0`)
only tripped on the 2nd request — but single-test runs only make 1
request, so the test always passed.

These tests pin the fixture-scenario invariants as property assertions
on the fixture's server source, so future edits can't accidentally
re-introduce either bug.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_JS = REPO_ROOT / "scripts" / "tests" / "fixtures" / "playwright-demo" / "app" / "server.js"

# Playwright's default expect auto-retry timeout. The timing scenario's
# server delay MUST be greater than this — otherwise toHaveCount and
# similar auto-retrying assertions will succeed despite the delay.
PLAYWRIGHT_EXPECT_DEFAULT_TIMEOUT_MS = 5000


@pytest.fixture(scope="module")
def server_source() -> str:
    """Read the fixture server's source code once for all property tests."""
    assert SERVER_JS.is_file(), f"fixture missing: {SERVER_JS}"
    return SERVER_JS.read_text(encoding="utf-8")


class TestTimingScenarioInvariant:
    """Bug 13 regression pin: timing scenario must produce a failure under
    Playwright's default expect timeout."""

    def test_timing_delay_exceeds_playwright_default_timeout(self, server_source):
        """Extract the `timing` scenario's delay literal and assert it's
        greater than Playwright's default expect timeout. Otherwise the
        test would pass via auto-retry and we'd lose the TIMING scenario
        entirely.

        Accepts two forms:
        - Ternary: `SCENARIO === 'timing' ? 8000 : 0`
        - Block constant: `if (SCENARIO === 'timing') { const DELAY = 8000; ... }`
        """
        delay_ms: int | None = None

        # Form 1: ternary
        ternary = re.search(
            r"SCENARIO\s*===\s*['\"]timing['\"]\s*\?\s*(\d+)\s*:",
            server_source,
        )
        if ternary:
            delay_ms = int(ternary.group(1))

        # Form 2: `if (SCENARIO === 'timing') { ... const FOO = <N>; ... setTimeout(..., FOO) }`
        # OR directly: setTimeout(r, <N>) inside the timing block.
        if delay_ms is None:
            block = re.search(
                r"if\s*\(\s*SCENARIO\s*===\s*['\"]timing['\"]\s*\)\s*\{([\s\S]*?)^\s*\}",
                server_source,
                re.MULTILINE,
            )
            if block:
                body = block.group(1)
                # Look for a numeric literal > 4 digits (>= 1000ms) assigned or
                # passed to setTimeout.
                numeric = re.search(
                    r"(?:=\s*|setTimeout\s*\([^,]+,\s*)(\d{4,})",
                    body,
                )
                if numeric:
                    delay_ms = int(numeric.group(1))

        assert delay_ms is not None, (
            "Could not locate a timing-scenario delay value in server.js. "
            "Expected either `SCENARIO === 'timing' ? <ms> : 0` (ternary) or "
            "`if (SCENARIO === 'timing') { ... <ms>... }` (block form)."
        )
        assert delay_ms > PLAYWRIGHT_EXPECT_DEFAULT_TIMEOUT_MS, (
            f"timing scenario delay is {delay_ms}ms; must exceed Playwright's "
            f"default expect timeout ({PLAYWRIGHT_EXPECT_DEFAULT_TIMEOUT_MS}ms) "
            "so the test fails instead of passing via auto-retry. "
            "Recommended: 8000ms."
        )


class TestFlakyScenarioInvariant:
    """Bug 14 regression pin: flaky scenario must intermittently fail on
    the FIRST request of a fresh server, since each test run makes a
    single /api/metric request against a freshly-started server."""

    def test_flaky_logic_is_intermittent_not_even_only(self, server_source):
        """The original logic was `counter % 2 === 0` — fails on even
        counts only. Since tests make one request (counter=1), failure
        never fired. Rewrite must fire intermittently on counter=1 OR
        use randomness so failures can occur on the first request."""
        # Locate the flaky scenario's response-decision block.
        # We look for the broader `if (SCENARIO === 'flaky')` block.
        flaky_block_match = re.search(
            r"if\s*\(\s*SCENARIO\s*===\s*['\"]flaky['\"]\s*\)\s*\{([\s\S]*?)^\s*\}",
            server_source,
            re.MULTILINE,
        )
        assert flaky_block_match, (
            "Could not locate the `if (SCENARIO === 'flaky')` block in server.js."
        )
        block = flaky_block_match.group(1)

        # The pure `counter % 2 === 0` idiom (fires only on even counter)
        # is the known-bad pattern. If only this expression gates failure,
        # first requests always pass.
        pure_even_only = re.search(r"counter\s*%\s*2\s*===?\s*0\s*\)", block)
        assert not pure_even_only, (
            "flaky scenario uses `counter % 2 === 0` which only fires on "
            "even counts — but tests make only 1 request, so counter=1 is odd "
            "and the failure never triggers. Use `Math.random()` or trip on "
            "odd counts so the first request can fail."
        )

        # Require at least one genuinely intermittent signal in the block:
        # either randomness (Math.random) or an odd-counter / first-request
        # trigger.
        has_random = "Math.random" in block
        has_odd_or_first_trigger = bool(
            re.search(r"counter\s*%\s*2\s*(===?|!==?)\s*1", block)
            or re.search(r"counter\s*===?\s*1\b", block)
            or re.search(r"counter\s*<=?\s*\d", block)
        )
        assert has_random or has_odd_or_first_trigger, (
            "flaky scenario must either use Math.random() for true intermittency "
            "OR trigger the 500 on the first request (counter === 1 / "
            "counter % 2 === 1) so single-test runs can fail."
        )


class TestScenarioMatrixCoverage:
    """Sanity-check that every documented scenario has a handler."""

    REQUIRED_SCENARIOS = ["pass", "broken-locator", "timing", "visual-change",
                         "logic", "flaky", "infra"]

    def test_every_required_scenario_is_referenced(self, server_source):
        for scenario in self.REQUIRED_SCENARIOS:
            assert scenario in server_source, (
                f"scenario {scenario!r} not referenced in server.js"
            )
