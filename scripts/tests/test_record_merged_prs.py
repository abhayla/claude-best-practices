"""Tests for the zero-manual merged-PR trust recorder (scripts/record_merged_prs.py).

Never calls real `gh` — every test injects a fake `gh` runner that returns canned JSON,
matching the module's design (every gh access goes through an injectable `gh(args) -> str`).
"""

import json
import subprocess

from scripts.trust_score import load_ledger, stats_by
from scripts import record_merged_prs as rmp


def _rollup_success():
    return [{"name": "validate", "conclusion": "SUCCESS"}]


def _rollup_failure():
    return [{"name": "validate", "conclusion": "FAILURE"}]


def _pr(number, body="", branch="auto/work-1", commits=None, reviews=None, rollup=None):
    return {
        "number": number,
        "headRefName": branch,
        "title": f"PR {number}",
        "body": body,
        "mergedAt": "2026-07-10T00:00:00Z",
        "commits": commits if commits is not None else [{"messageHeadline": "add feature"}],
        "reviews": reviews if reviews is not None else [],
        "statusCheckRollup": rollup if rollup is not None else _rollup_success(),
    }


def _fake_gh(list_numbers, pr_by_number):
    """Build an injectable gh(args) -> str callable from canned data."""

    def gh(args):
        if args[:2] == ["pr", "list"]:
            return json.dumps([{"number": n} for n in list_numbers])
        if args[:2] == ["pr", "view"]:
            number = int(args[2])
            return json.dumps(pr_by_number[number])
        raise AssertionError(f"unexpected gh args: {args}")

    return gh


class TestGreenVerifiedPR:
    def test_recorded_as_auto_with_full_fields(self, tmp_path):
        marker = tmp_path / ".recorded-prs"
        ledger = tmp_path / "atlas.jsonl"
        pr = _pr(317, body="Fixes the thing.\n\nVerified-by: code-reviewer-agent\n", branch="auto/work-317")
        gh = _fake_gh([317], {317: pr})

        outcome = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)

        assert outcome["recorded"] == [317]
        assert outcome["skipped"] == 0
        assert outcome["results"][317] == {"score": 85, "recommended": "AUTO"}

        runs = load_ledger(ledger)
        assert len(runs) == 1
        entry = runs[0]
        assert entry["pr"] == 317
        assert entry["branch"] == "auto/work-317"
        assert entry["skill"] == "branch:auto"
        assert "recorded_at" in entry
        assert entry["score"] == 85
        assert entry["recommended"] == "AUTO"


class TestGreenUnverifiedPR:
    def test_recorded_as_escalate_honest_no_verification(self, tmp_path):
        marker = tmp_path / ".recorded-prs"
        ledger = tmp_path / "atlas.jsonl"
        pr = _pr(318, body="Fixes another thing, no review marker.", branch="fix/thing")
        gh = _fake_gh([318], {318: pr})

        outcome = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)

        assert outcome["results"][318] == {"score": 60, "recommended": "ESCALATE"}
        runs = load_ledger(ledger)
        assert runs[0]["skill"] == "branch:fix"


class TestPlantedFalseDoneTrap:
    def test_planted_false_done_is_vetoed_by_hard_gate(self, tmp_path):
        """A liar plants BOTH a false completion claim AND a Verified-by marker in the PR
        body, but the required `validate` check actually FAILED. The hard gate on
        tests_pass/secret_scan_clean must veto AUTO regardless of the verification +
        production_health weight (0.25 + 0.10 = 0.35 alone can never clear the bar)."""
        marker = tmp_path / ".recorded-prs"
        ledger = tmp_path / "atlas.jsonl"
        pr = _pr(
            319,
            body="All tests pass — done!\n\nVerified-by: builder\n",
            branch="auto/work-319",
            rollup=_rollup_failure(),
        )
        gh = _fake_gh([319], {319: pr})

        outcome = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)

        result_summary = outcome["results"][319]
        assert result_summary["recommended"] == "ESCALATE"

        runs = load_ledger(ledger)
        entry = runs[0]
        assert entry["recommended"] == "ESCALATE"
        # Re-derive the full result to inspect hard_gate_triggered + reasons (not stored
        # verbatim in the ledger entry, only score/recommended/human_had_to_fix/stage).
        from scripts.collect_signals import assemble_signals
        from scripts.trust_score import compute_trust_score, load_config

        signals = assemble_signals(
            tests_passed=0,
            tests_total=1,
            coverage=0.0,
            independent_verification=rmp.independent_verification(pr),
            regression_clean=0.0,
            production_health=1.0,
            secret_scan_clean=0.0,
        )
        config = load_config(rmp.CONFIG_PATH)
        result = compute_trust_score(signals, config, stage="reversible")
        assert result["hard_gate_triggered"] is True
        assert any("hard gate" in r for r in result["reasons"])
        assert result["score"] < config["threshold"]


class TestIdempotency:
    def test_second_sweep_with_marker_records_nothing_new(self, tmp_path):
        marker = tmp_path / ".recorded-prs"
        ledger = tmp_path / "atlas.jsonl"
        pr = _pr(320, body="Verified-by: code-reviewer-agent")
        gh = _fake_gh([320], {320: pr})

        first = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)
        assert first["recorded"] == [320]

        second = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)
        assert second["recorded"] == []
        assert second["skipped"] == 1
        assert len(load_ledger(ledger)) == 1

    def test_fresh_marker_but_existing_ledger_entry_records_nothing_new(self, tmp_path):
        """Belt-and-suspenders dedup: even with a brand-new marker file, a PR number
        already present as a `pr` field in the ledger must not be re-recorded."""
        marker = tmp_path / ".recorded-prs"  # never touched — simulates a wiped marker
        ledger = tmp_path / "atlas.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(json.dumps({"pr": 321, "score": 85, "recommended": "AUTO"}) + "\n", encoding="utf-8")

        pr = _pr(321, body="Verified-by: code-reviewer-agent")
        gh = _fake_gh([321], {321: pr})

        outcome = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)
        assert outcome["recorded"] == []
        assert outcome["skipped"] == 1
        assert len(load_ledger(ledger)) == 1


class TestDeriveHumanHadToFix:
    def test_two_commits_is_true(self):
        pr = _pr(1, commits=[{"messageHeadline": "add feature"}, {"messageHeadline": "oops typo"}])
        assert rmp.derive_human_had_to_fix(pr) is True

    def test_one_clean_commit_is_false(self):
        pr = _pr(1, commits=[{"messageHeadline": "add feature"}])
        assert rmp.derive_human_had_to_fix(pr) is False

    def test_one_fix_commit_is_true(self):
        pr = _pr(1, commits=[{"messageHeadline": "fix: broken import"}])
        assert rmp.derive_human_had_to_fix(pr) is True

    def test_zero_commits_is_none(self):
        pr = _pr(1, commits=[])
        assert rmp.derive_human_had_to_fix(pr) is None


class TestStatsBy:
    def test_groups_by_skill(self, tmp_path):
        ledger = tmp_path / "atlas.jsonl"
        marker = tmp_path / ".recorded-prs"
        pr_a = _pr(1, body="Skill: alpha", branch="auto/work-1")
        pr_b = _pr(2, body="", branch="beta/work-2")
        gh = _fake_gh([1, 2], {1: pr_a, 2: pr_b})

        rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)

        runs = load_ledger(ledger)
        by_skill = stats_by(runs, "skill")
        assert set(by_skill.keys()) == {"alpha", "branch:beta"}
        assert by_skill["alpha"]["total_runs"] == 1
        assert by_skill["branch:beta"]["total_runs"] == 1


class TestValidateCheckPassed:
    def test_check_run_shape_success(self):
        pr = _pr(1, rollup=[{"name": "validate", "conclusion": "SUCCESS"}])
        assert rmp.validate_check_passed(pr) is True

    def test_status_context_shape_success(self):
        pr = _pr(1, rollup=[{"context": "validate", "state": "SUCCESS"}])
        assert rmp.validate_check_passed(pr) is True

    def test_check_run_shape_failure(self):
        pr = _pr(1, rollup=[{"name": "validate", "conclusion": "FAILURE"}])
        assert rmp.validate_check_passed(pr) is False

    def test_missing_validate_entry_is_false(self):
        pr = _pr(1, rollup=[{"name": "other-check", "conclusion": "SUCCESS"}])
        assert rmp.validate_check_passed(pr) is False


class TestDeriveSkill:
    def test_explicit_skill_line_wins(self):
        pr = _pr(1, body="Skill: my-cool-skill\n", branch="auto/work-1")
        assert rmp.derive_skill(pr) == "my-cool-skill"

    def test_branch_prefix_fallback(self):
        pr = _pr(1, body="", branch="fix/something")
        assert rmp.derive_skill(pr) == "branch:fix"

    def test_no_slash_in_branch_is_none(self):
        pr = _pr(1, body="", branch="main-fixup")
        assert rmp.derive_skill(pr) is None


class TestHangGuards:
    def test_gh_timeout_on_one_pr_skips_it_and_sweep_continues(self, tmp_path):
        """A gh timeout (or any per-PR error) must skip THAT PR, never crash the sweep."""
        marker = tmp_path / ".recorded-prs"
        ledger = tmp_path / "atlas.jsonl"
        good_pr = _pr(402, body="Verified-by: code-reviewer-agent", branch="auto/work-402")

        def gh(args):
            if args[:2] == ["pr", "list"]:
                return json.dumps([{"number": 401}, {"number": 402}])
            if args[:2] == ["pr", "view"]:
                if int(args[2]) == 401:
                    raise subprocess.TimeoutExpired(cmd="gh pr view 401", timeout=20)
                return json.dumps(good_pr)
            raise AssertionError(f"unexpected gh args: {args}")

        outcome = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)

        assert outcome["recorded"] == [402]
        assert outcome["skipped"] == 1
        assert "aborted" not in outcome
        assert len(load_ledger(ledger)) == 1

    def test_sweep_deadline_aborts_gracefully(self, tmp_path, monkeypatch):
        """Once the sweep deadline passes, remaining PRs are left for the next session's
        sweep and the summary carries `aborted: deadline`."""
        marker = tmp_path / ".recorded-prs"
        ledger = tmp_path / "atlas.jsonl"
        pr_a = _pr(501, body="Verified-by: code-reviewer-agent", branch="auto/work-501")
        pr_b = _pr(502, body="Verified-by: code-reviewer-agent", branch="auto/work-502")
        gh = _fake_gh([501, 502], {501: pr_a, 502: pr_b})

        # Fake clock: the deadline is computed on the first call; the second iteration's
        # check sees a time already past it, so only PR 501 gets processed.
        ticks = iter([0.0, 0.0, 1000.0, 1000.0, 1000.0])
        monkeypatch.setattr(rmp.time, "monotonic", lambda: next(ticks))

        outcome = rmp.record_merged_prs(limit=15, marker_path=marker, ledger_path=ledger, gh=gh)

        assert outcome["aborted"] == "deadline"
        assert outcome["recorded"] == [501]
        assert len(load_ledger(ledger)) == 1

    def test_default_gh_runner_has_a_timeout(self):
        """The real _gh must pass a timeout to subprocess.run (hang guard for the hook)."""
        import inspect

        sig = inspect.signature(rmp._gh)
        assert sig.parameters["timeout"].default == rmp.GH_TIMEOUT_SECONDS
