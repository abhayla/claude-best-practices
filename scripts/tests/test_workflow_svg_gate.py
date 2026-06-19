"""Tests for the --require-svg gate behavior in generate_workflow_docs.py (issue #127).

The gate must NOT hard-fail the docs job over a single workflow whose diagrams can't
render (mmdc present but a content quirk) — it WARNS + logs (no silent truncation).
The mmdc-*presence* guarantee stays in `check_svg_requirements`; a *total* render
breakage is caught separately by the caller. This pins the warn-not-exit contract so
the loop-engineering case (0/29 SVGs on CI) can't re-red the maintenance workflow.
"""

import pytest

from scripts.generate_workflow_docs import validate_svg_output


def _make_svgs(images_dir, workflow_name, n):
    images_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        (images_dir / f"{workflow_name}-{i}.svg").write_text("<svg/>", encoding="utf-8")


def test_returns_true_when_all_svgs_present(tmp_path):
    _make_svgs(tmp_path, "wf", 5)
    assert validate_svg_output("wf", tmp_path, expected_count=5) is True


def test_warns_and_returns_false_on_shortfall_WITHOUT_exiting(tmp_path):
    """The load-bearing fix: a render shortfall must NOT call sys.exit — it warns + returns False."""
    _make_svgs(tmp_path, "wf", 2)
    # Must NOT raise SystemExit (the old behavior); must return False.
    result = validate_svg_output("wf", tmp_path, expected_count=29)
    assert result is False


def test_zero_rendered_returns_false_not_exit(tmp_path):
    """The exact loop-engineering/CI case: 0 of N rendered → warn (False), never exit."""
    (tmp_path / "images").mkdir()
    result = validate_svg_output("loop-engineering", tmp_path / "images", expected_count=29)
    assert result is False  # and crucially: no SystemExit was raised


def test_no_systemexit_is_raised_on_gap(tmp_path):
    """Belt-and-suspenders: explicitly assert SystemExit is not raised."""
    _make_svgs(tmp_path, "wf", 0)
    try:
        validate_svg_output("wf", tmp_path, expected_count=10)
    except SystemExit:  # pragma: no cover
        pytest.fail("validate_svg_output must not sys.exit on a render shortfall (issue #127)")
