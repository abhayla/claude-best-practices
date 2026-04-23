"""LOGIC_BUG fixture for the three-lane test pipeline (PR1).

A simple Python pytest with a deliberate logic bug. Per scout's classification:
- Path: `tests/unit/` → does NOT match API path globs
- Imports: no HTTP client, no UI test framework imports
- Result: only the `functional` track is required for this test

The test ITSELF fails (assertion error) — this is a deliberate failure used
to verify:
- T1's extended inline Issue creation handles `LOGIC_BUG` category (existing pre-PR1 behavior)
- The auto-fix matrix correctly classifies this as `ISSUE_ONLY` (no auto-heal attempt)
- Per-test gate evaluates: required = ["functional"], functional verdict = FAILED → overall FAIL

Used by:
- `scripts/tests/test_pipeline_three_lane.py::test_per_test_gate_functional_only`
"""


def add(a: int, b: int) -> int:
    """DELIBERATE LOGIC BUG: subtracts instead of adds."""
    return a - b   # noqa — the bug is the point


def test_add_two_plus_three_equals_five():
    """Should pass — fails because of the bug in `add()` above.

    The healer agent must NOT attempt to auto-fix this test (the bug is in
    the source, not the test) — `LOGIC_BUG` category is `ISSUE_ONLY` per
    the auto-fix authority matrix in spec §3.6.
    """
    assert add(2, 3) == 5
