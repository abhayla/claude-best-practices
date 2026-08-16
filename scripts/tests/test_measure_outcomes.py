"""Fixture tests for the outcome scorecard.

Every expected value here is HAND-COMPUTABLE from the fixture above it — that is the
point. A metric whose expected value can only be produced by running the code it tests
proves nothing, so each fixture is small enough to verify with arithmetic in your head
(the DoD's worked example: 2 of 10 PRs re-fixed MUST be exactly 0.20).
"""

import pytest

from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.measure_outcomes import (
    change_failure_rate,
    cost_per_task,
    first_pass_rate,
    guardrail_catches,
    invocation_adoption,
    measure_all,
    rework_rate,
)

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _stamp(day_offset: int) -> str:
    return (BASE + timedelta(days=day_offset)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pr(number, day, title="feat: add thing", paths=("a.py",), commits=1,
        headlines=None, checks=("SUCCESS",), body=""):
    """Build a PR record in the shape `gh pr list --json` returns."""
    if headlines is None:
        headlines = [title] * commits
    return {
        "number": number,
        "title": title,
        "body": body,
        "mergedAt": _stamp(day),
        "files": [{"path": p} for p in paths],
        "commits": [{"messageHeadline": h} for h in headlines],
        "statusCheckRollup": [{"conclusion": c} for c in checks],
    }


class TestChangeFailureRate:
    def test_two_of_ten_refixed_is_exactly_020(self):
        """The DoD's worked example: 10 eligible PRs, 2 later fixed -> exactly 0.20.

        Hand-computation: originals merge on days 1..10; the newest PR merges on day 40,
        so the eligibility cutoff is day 10 and exactly those ten are old enough to
        judge. Fix PRs on days 25 and 26 repair mod3 and mod7 — both inside those PRs'
        30-day windows — so 2 of the 10 failed. 2/10 = 0.20. The fixes and the day-40 PR
        are themselves too recent to judge and stay out of the denominator.
        """
        prs = [_pr(i, day=i, paths=(f"mod{i}.py",)) for i in range(1, 11)]
        # Fix PRs land on days 25/26 — inside each original's 30-day window.
        prs.append(_pr(101, day=25, title="fix: repair mod3", paths=("mod3.py",)))
        prs.append(_pr(102, day=26, title="fix: repair mod7", paths=("mod7.py",)))
        # Reference PR at day 40 puts the cutoff at day 10: exactly the ten originals are
        # eligible (days 1..10), while the two fixes (days 25/26) and this PR are too
        # recent to have had a full window and are excluded from the denominator.
        prs.append(_pr(103, day=40, title="chore: unrelated", paths=("zzz.py",)))

        result = change_failure_rate(prs, window_days=30)
        assert result["sample_size"] == 10
        assert result["failed"] == 2
        assert result["value"] == 0.20

    def test_fix_touching_different_files_is_not_a_failure(self):
        """A fix-shaped PR sharing no files is repairing something else."""
        prs = [
            _pr(1, day=1, paths=("alpha.py",)),
            _pr(2, day=5, title="fix: repair beta", paths=("beta.py",)),
            _pr(3, day=100, title="chore: later", paths=("gamma.py",)),
        ]
        result = change_failure_rate(prs, window_days=30)
        assert result["failed"] == 0
        assert result["value"] == 0.0

    def test_same_file_but_not_fix_shaped_is_not_a_failure(self):
        """Ordinary iteration on the same file is rework, not a change failure."""
        prs = [
            _pr(1, day=1, paths=("alpha.py",)),
            _pr(2, day=5, title="feat: extend alpha", paths=("alpha.py",)),
            _pr(3, day=100, title="chore: later", paths=("gamma.py",)),
        ]
        assert change_failure_rate(prs, window_days=30)["failed"] == 0

    def test_fix_outside_window_does_not_count(self):
        prs = [
            _pr(1, day=1, paths=("alpha.py",)),
            _pr(2, day=90, title="fix: repair alpha", paths=("alpha.py",)),
            _pr(3, day=200, title="chore: later", paths=("gamma.py",)),
        ]
        assert change_failure_rate(prs, window_days=30)["failed"] == 0

    def test_recent_prs_excluded_from_denominator_not_counted_clean(self):
        """PRs without a full elapsed window must not silently deflate the rate."""
        prs = [_pr(i, day=100 + i, paths=(f"m{i}.py",)) for i in range(3)]
        result = change_failure_rate(prs, window_days=30)
        assert result["value"] is None
        assert result["sample_size"] == 0
        assert "old enough" in result["note"]

    def test_empty_input_reports_no_data(self):
        result = change_failure_rate([], window_days=30)
        assert result["value"] is None and result["sample_size"] == 0

    def test_pr_cannot_fail_itself(self):
        """A single fix-shaped PR must not mark itself as its own failure."""
        prs = [
            _pr(1, day=1, title="fix: repair alpha", paths=("alpha.py",)),
            _pr(2, day=100, title="chore: later", paths=("z.py",)),
        ]
        assert change_failure_rate(prs, window_days=30)["failed"] == 0


class TestReworkRate:
    def test_one_of_four_reworked_is_exactly_025(self):
        """Originals on days 1..4; newest on day 34 puts the cutoff at day 4, so exactly
        those four are eligible. The day-20 PR re-touches f2, reworking 1 of 4 = 0.25."""
        prs = [_pr(i, day=i, paths=(f"f{i}.py",)) for i in range(1, 5)]
        prs.append(_pr(50, day=20, title="feat: revisit f2", paths=("f2.py",)))
        prs.append(_pr(99, day=34, title="chore: later", paths=("zzz.py",)))
        result = rework_rate(prs, window_days=30)
        assert result["sample_size"] == 4
        assert result["reworked"] == 1
        assert result["value"] == 0.25

    def test_counts_non_fix_churn_unlike_cfr(self):
        """Rework counts ANY re-touch; change-failure-rate counts only fix-shaped ones."""
        prs = [
            _pr(1, day=1, paths=("alpha.py",)),
            _pr(2, day=5, title="feat: extend alpha", paths=("alpha.py",)),
            _pr(3, day=200, title="chore: later", paths=("gamma.py",)),
        ]
        assert rework_rate(prs, window_days=30)["reworked"] == 1
        assert change_failure_rate(prs, window_days=30)["failed"] == 0

    def test_pr_without_files_is_excluded_not_counted_clean(self):
        prs = [
            _pr(1, day=1, paths=()),
            _pr(2, day=2, paths=("b.py",)),
            _pr(3, day=200, title="chore: later", paths=("zzz.py",)),
        ]
        result = rework_rate(prs, window_days=30)
        assert result["sample_size"] == 1


class TestFirstPassRate:
    def test_three_of_four_first_pass_is_exactly_075(self):
        prs = [
            _pr(1, day=1, commits=1),
            _pr(2, day=2, commits=1),
            _pr(3, day=3, commits=1),
            _pr(4, day=4, commits=2, headlines=["feat: x", "fix: correct x"]),
        ]
        result = first_pass_rate(prs)
        assert result["sample_size"] == 4
        assert result["first_pass"] == 3
        assert result["value"] == 0.75

    def test_single_fix_shaped_commit_is_not_first_pass(self):
        prs = [_pr(1, day=1, commits=1, headlines=["fix: repair the thing"])]
        assert first_pass_rate(prs)["value"] == 0.0

    def test_pr_without_commits_excluded(self):
        prs = [_pr(1, day=1, commits=1), {"number": 2, "commits": []}]
        assert first_pass_rate(prs)["sample_size"] == 1

    def test_no_commit_data_reports_no_data(self):
        assert first_pass_rate([{"number": 1, "commits": []}])["value"] is None


class TestGuardrailCatches:
    def test_counts_only_red_then_fixed(self):
        prs = [
            # Confirmed catch: went red, ended green.
            _pr(1, day=1, checks=("FAILURE", "SUCCESS")),
            # Never red — not a catch (a gate that never fires earns nothing).
            _pr(2, day=2, checks=("SUCCESS",)),
            # Confirmed catch via a repair commit.
            _pr(3, day=3, checks=("FAILURE",), commits=2,
                headlines=["feat: x", "fix: repair ci"]),
        ]
        result = guardrail_catches(prs)
        assert result["value"] == 2
        assert result["sample_size"] == 3

    def test_blocking_everything_cannot_inflate_the_metric(self):
        """ANTI-GAMING: reds with no ensuing repair are noise, not catches."""
        prs = [_pr(i, day=i, checks=("FAILURE",), commits=1,
                   headlines=["feat: unrelated"]) for i in range(1, 6)]
        assert guardrail_catches(prs)["value"] == 0

    def test_all_green_reports_zero_not_a_perfect_score(self):
        prs = [_pr(i, day=i, checks=("SUCCESS",)) for i in range(1, 4)]
        assert guardrail_catches(prs)["value"] == 0


class TestInvocationAdoption:
    def test_reads_measured_log_when_present(self, tmp_path: Path):
        log = tmp_path / "invocations.jsonl"
        log.write_text(
            '{"skill": "code-review"}\n{"skill": "code-review"}\n{"skill": "fix-loop"}\n',
            encoding="utf-8",
        )
        result = invocation_adoption(log, [])
        assert result["value"] == {"code-review": 2, "fix-loop": 1}
        assert result["sample_size"] == 3
        assert "measured" in result["source"]

    def test_absent_log_reports_no_data_never_a_fabricated_rate(self, tmp_path: Path):
        """The tautology this replaces reported 1.0 from a sample of 1."""
        result = invocation_adoption(tmp_path / "missing.jsonl", [])
        assert result["value"] is None
        assert result["sample_size"] == 0
        assert "NO DATA" in result["note"]

    def test_falls_back_to_pr_attribution_labelled_as_weaker(self):
        prs = [_pr(1, day=1, body="Skill: test-pipeline\n")]
        result = invocation_adoption(None, prs)
        assert result["value"] == {"test-pipeline": 1}
        assert "self-asserted" in result["source"]

    def test_malformed_log_lines_are_skipped_not_fatal(self, tmp_path: Path):
        log = tmp_path / "invocations.jsonl"
        log.write_text('{"skill": "a"}\nNOT JSON\n\n{"skill": "a"}\n', encoding="utf-8")
        assert invocation_adoption(log, [])["value"] == {"a": 2}


class TestCostPerTask:
    def test_divides_spend_by_completed_prs(self):
        costs = [
            {"date": "2026-01-02", "usd": 60.0},
            {"date": "2026-01-03", "usd": 40.0},
        ]
        prs = [_pr(1, day=1), _pr(2, day=2), _pr(3, day=2), _pr(4, day=1)]
        result = cost_per_task(costs, prs, days=30)
        # $100 total across 4 PRs merged on those dates -> exactly $25.00 per PR.
        assert result["usd"] == 100.0
        assert result["sample_size"] == 4
        assert result["value"] == 25.0

    def test_absent_ledger_reports_no_data(self):
        assert cost_per_task([], [_pr(1, day=1)], days=30)["value"] is None

    def test_no_prs_in_window_is_undefined_not_zero(self):
        costs = [{"date": "2026-01-02", "usd": 60.0}]
        result = cost_per_task(costs, [], days=30)
        assert result["value"] is None
        assert "undefined" in result["note"]


class TestMeasureAll:
    def test_reports_all_six_metrics(self):
        report = measure_all([_pr(1, day=1)], [], 30, None)
        assert set(report["metrics"]) == {
            "change_failure_rate", "rework_rate", "first_pass_rate",
            "guardrail_catches", "invocation_adoption", "cost_per_task",
        }

    def test_survives_completely_empty_input(self):
        """No data anywhere must produce honest Nones, never a crash or a fake number."""
        report = measure_all([], [], 30, None)
        for name, metric in report["metrics"].items():
            if name == "guardrail_catches":
                assert metric["value"] == 0  # a count, honestly zero
            else:
                assert metric["value"] is None

    def test_reports_no_pass_fail_judgment(self):
        """Baseline pass: the scorecard measures, it does not grade."""
        report = measure_all([_pr(1, day=1)], [], 30, None)
        blob = str(report).lower()
        for verdict in ("passed", "failed_gate", "verdict", "threshold"):
            assert verdict not in blob


class TestFetchHonesty:
    """A failed READ must never be reported as a measured absence of data (T-144).

    Observed for real while building this: PR bodies are huge, fetching 100 of them blew
    the timeout, and the scorecard silently reported all-zeroes as if measured.
    """

    def test_timeout_raises_rather_than_returning_empty(self, monkeypatch):
        import subprocess as sp
        from scripts import measure_outcomes as mo

        def boom(*a, **k):
            raise sp.TimeoutExpired(cmd="gh", timeout=1)

        monkeypatch.setattr(mo.subprocess, "run", boom)
        with pytest.raises(mo.FetchError, match="timed out"):
            mo.fetch_merged_prs()

    def test_nonzero_exit_raises(self, monkeypatch):
        from scripts import measure_outcomes as mo

        class R:
            returncode = 1
            stdout = ""
            stderr = "not authenticated"

        monkeypatch.setattr(mo.subprocess, "run", lambda *a, **k: R())
        with pytest.raises(mo.FetchError, match="not authenticated"):
            mo.fetch_merged_prs()

    def test_bad_json_raises(self, monkeypatch):
        from scripts import measure_outcomes as mo

        class R:
            returncode = 0
            stdout = "{not json"
            stderr = ""

        monkeypatch.setattr(mo.subprocess, "run", lambda *a, **k: R())
        with pytest.raises(mo.FetchError):
            mo.fetch_merged_prs()

    def test_empty_history_is_a_finding_not_an_error(self, monkeypatch):
        """Genuinely zero merged PRs reads fine and returns [] — no exception."""
        from scripts import measure_outcomes as mo

        class R:
            returncode = 0
            stdout = "[]"
            stderr = ""

        monkeypatch.setattr(mo.subprocess, "run", lambda *a, **k: R())
        assert mo.fetch_merged_prs() == []

    def test_telemetry_records_fetch_failure_distinctly(self, monkeypatch):
        from scripts import aggregate_telemetry as at
        from scripts import measure_outcomes as mo

        def boom(*a, **k):
            raise mo.FetchError("gh timed out after 120s")

        monkeypatch.setattr(mo, "fetch_merged_prs", boom)
        result = at.collect_outcomes()
        assert "could not read PR history" in result["unavailable"]
