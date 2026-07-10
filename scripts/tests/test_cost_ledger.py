"""Tests for the self-enforcing cost ledger (scripts/cost_ledger.py).

Never touches the real `~/.claude/projects/` tree or the network — every test builds a
synthetic transcript fixture under `tmp_path` and injects a fake `notify` for alerting.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from scripts import cost_ledger as cl

CONFIG = {
    "families": {
        "opus": {"input": 15.00, "output": 75.00, "cache_write": 18.75, "cache_read": 1.50},
        "sonnet": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
        "haiku": {"input": 0.80, "output": 4.00, "cache_write": 1.00, "cache_read": 0.08},
        "default": {"input": 15.00, "output": 75.00, "cache_write": 18.75, "cache_read": 1.50},
    },
    "daily_alert_usd": 50,
    "ledger_retention_days": 365,
}


def _entry(model, timestamp, usage, attribution=None, session_id="sess-1"):
    message = {"model": model, "usage": usage}
    entry = {"message": message, "timestamp": timestamp, "sessionId": session_id}
    if attribution:
        entry["attributionAgent"] = attribution
    return entry


def _write_jsonl(path: Path, lines: list[dict | str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            if isinstance(line, str):
                f.write(line + "\n")
            else:
                f.write(json.dumps(line) + "\n")


class TestScanTranscripts:
    def test_skips_lines_without_usage(self, tmp_path):
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [
                {"type": "user", "message": {"role": "user", "content": "hi"}, "timestamp": "2026-07-01T00:00:00Z"},
                _entry("claude-sonnet-4", "2026-07-01T00:01:00Z", {"input_tokens": 100, "output_tokens": 50}),
            ],
        )
        stats = {}
        entries = list(cl.scan_transcripts(tmp_path, stats=stats))
        assert len(entries) == 1
        assert stats["skipped_lines"] == 0  # the userless line has no usage — silently uninteresting, not malformed

    def test_counts_malformed_lines_as_skipped(self, tmp_path):
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [
                "{not valid json",
                _entry("claude-sonnet-4", "2026-07-01T00:00:00Z", {"input_tokens": 10, "output_tokens": 5}),
            ],
        )
        stats = {}
        entries = list(cl.scan_transcripts(tmp_path, stats=stats))
        assert len(entries) == 1
        assert stats["skipped_lines"] == 1

    def test_discovers_subagent_transcripts(self, tmp_path):
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [_entry("claude-sonnet-4", "2026-07-01T00:00:00Z", {"input_tokens": 10, "output_tokens": 5})],
        )
        _write_jsonl(
            project / "session-a" / "subagents" / "agent-1.jsonl",
            [
                _entry(
                    "claude-haiku-4",
                    "2026-07-01T00:05:00Z",
                    {"input_tokens": 20, "output_tokens": 8},
                    attribution="code-reviewer-agent",
                )
            ],
        )
        entries = list(cl.scan_transcripts(tmp_path))
        assert len(entries) == 2
        attributions = {e[3] for e in entries}
        assert attributions == {"main", "code-reviewer-agent"}

    def test_missing_projects_dir_yields_nothing(self, tmp_path):
        entries = list(cl.scan_transcripts(tmp_path / "does-not-exist"))
        assert entries == []

    def test_bad_file_is_skipped_not_fatal(self, tmp_path):
        project = tmp_path / "myproj"
        project.mkdir(parents=True)
        bad_dir_named_as_file_target = project / "not-a-real-file.jsonl"
        bad_dir_named_as_file_target.mkdir()  # a directory where a file is expected
        entries = list(cl.scan_transcripts(tmp_path))
        assert entries == []


class TestPlantedUsageTotals:
    def test_planted_usage_totals_are_exact(self, tmp_path):
        """TRAP-TEST: plant known token counts across two models and two attributions on the
        same day; the aggregate must reproduce them to the token and the USD to the cent."""
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [
                _entry(
                    "claude-sonnet-4",
                    "2026-07-01T10:00:00Z",
                    {
                        "input_tokens": 1_000_000,
                        "output_tokens": 500_000,
                        "cache_creation_input_tokens": 200_000,
                        "cache_read_input_tokens": 100_000,
                    },
                    session_id="sess-main",
                ),
                _entry(
                    "claude-haiku-4",
                    "2026-07-01T11:00:00Z",
                    {"input_tokens": 500_000, "output_tokens": 250_000},
                    attribution="skill-evaluator-agent",
                    session_id="sess-main",
                ),
            ],
        )

        entries = list(cl.scan_transcripts(tmp_path))
        days = cl.aggregate(entries, CONFIG)
        day = days["2026-07-01"]

        # sonnet: 1M*$3 + 0.5M*$15 + 0.2M*$3.75 + 0.1M*$0.30 = 3 + 7.5 + 0.75 + 0.03 = 11.28
        # haiku:  0.5M*$0.80 + 0.25M*$4.00 = 0.40 + 1.00 = 1.40
        assert round(day["by_model"]["claude-sonnet-4"]["usd"], 2) == 11.28
        assert round(day["by_model"]["claude-haiku-4"]["usd"], 2) == 1.40
        assert round(day["usd"], 2) == 12.68

        assert day["tokens"]["input"] == 1_500_000
        assert day["tokens"]["output"] == 750_000
        assert day["tokens"]["cache_write"] == 200_000
        assert day["tokens"]["cache_read"] == 100_000

        assert day["by_attribution"]["main"]["input"] == 1_000_000
        assert day["by_attribution"]["skill-evaluator-agent"]["input"] == 500_000

        assert day["session_count"] == 1  # both entries share sess-main

    def test_unknown_model_falls_back_to_default_rate(self, tmp_path):
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [_entry("some-future-model-9", "2026-07-01T00:00:00Z", {"input_tokens": 1_000_000, "output_tokens": 0})],
        )
        entries = list(cl.scan_transcripts(tmp_path))
        days = cl.aggregate(entries, CONFIG)
        assert round(days["2026-07-01"]["usd"], 2) == 15.00  # default family input rate


class TestAppendDaily:
    def _seed(self, tmp_path, day_str, tokens=1_000_000):
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [_entry("claude-sonnet-4", f"{day_str}T00:00:00Z", {"input_tokens": tokens, "output_tokens": 0})],
        )

    def test_excludes_today(self, tmp_path):
        today = date(2026, 7, 10)
        self._seed(tmp_path, today.isoformat())
        ledger_path = tmp_path / "ledger.jsonl"
        outcome = cl.append_daily(ledger_path=ledger_path, projects_dir=tmp_path, config=CONFIG, today=today)
        assert outcome["appended"] == []
        assert cl.load_ledger(ledger_path) == []

    def test_appends_completed_day(self, tmp_path):
        today = date(2026, 7, 10)
        yesterday = today - timedelta(days=1)
        self._seed(tmp_path, yesterday.isoformat())
        ledger_path = tmp_path / "ledger.jsonl"
        outcome = cl.append_daily(ledger_path=ledger_path, projects_dir=tmp_path, config=CONFIG, today=today)
        assert outcome["appended"] == [yesterday.isoformat()]
        records = cl.load_ledger(ledger_path)
        assert len(records) == 1
        assert records[0]["date"] == yesterday.isoformat()

    def test_idempotent_rerun_adds_nothing(self, tmp_path):
        today = date(2026, 7, 10)
        yesterday = today - timedelta(days=1)
        self._seed(tmp_path, yesterday.isoformat())
        ledger_path = tmp_path / "ledger.jsonl"
        cl.append_daily(ledger_path=ledger_path, projects_dir=tmp_path, config=CONFIG, today=today)
        second = cl.append_daily(ledger_path=ledger_path, projects_dir=tmp_path, config=CONFIG, today=today)
        assert second["appended"] == []
        assert len(cl.load_ledger(ledger_path)) == 1

    def test_skipped_lines_reported(self, tmp_path):
        today = date(2026, 7, 10)
        yesterday = today - timedelta(days=1)
        project = tmp_path / "myproj"
        _write_jsonl(
            project / "session-a.jsonl",
            [
                "garbage not json",
                _entry("claude-sonnet-4", f"{yesterday.isoformat()}T00:00:00Z", {"input_tokens": 10, "output_tokens": 0}),
            ],
        )
        ledger_path = tmp_path / "ledger.jsonl"
        outcome = cl.append_daily(ledger_path=ledger_path, projects_dir=tmp_path, config=CONFIG, today=today)
        assert outcome["skipped_lines"] == 1


class TestCheckAlert:
    def test_fail_open_when_no_notifier_env(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTIFIER_URL", raising=False)
        monkeypatch.delenv("NOTIFIER_KEY", raising=False)
        today = date(2026, 7, 10)
        yesterday = today - timedelta(days=1)
        ledger_path = tmp_path / "ledger.jsonl"
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"date": yesterday.isoformat(), "usd": 999.0}) + "\n")

        captured = []

        def fake_notify(*args, **kwargs):
            captured.append((args, kwargs))

        result = cl.check_alert(ledger_path=ledger_path, config=CONFIG, today=today, notify=fake_notify)
        # cost_ledger's real notify() no-ops on unset env; here we verify the CALLER decides
        # to call notify() when over-threshold regardless of env (env-gating lives inside the
        # real _notify_owner, not check_alert) — so the injected fake IS invoked...
        assert result["alerted"] is True
        assert captured  # ...proving check_alert wires the alert path correctly

    def test_no_alert_under_threshold(self, tmp_path):
        today = date(2026, 7, 10)
        yesterday = today - timedelta(days=1)
        ledger_path = tmp_path / "ledger.jsonl"
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"date": yesterday.isoformat(), "usd": 1.0}) + "\n")

        captured = []
        result = cl.check_alert(ledger_path=ledger_path, config=CONFIG, today=today, notify=lambda *a, **k: captured.append(1))
        assert result["alerted"] is False
        assert not captured

    def test_no_alert_when_no_ledger_entry_for_yesterday(self, tmp_path):
        today = date(2026, 7, 10)
        ledger_path = tmp_path / "ledger.jsonl"  # no file at all
        captured = []
        result = cl.check_alert(ledger_path=ledger_path, config=CONFIG, today=today, notify=lambda *a, **k: captured.append(1))
        assert result["alerted"] is False
        assert not captured

    def test_real_notify_owner_fail_open_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("NOTIFIER_URL", raising=False)
        monkeypatch.delenv("NOTIFIER_KEY", raising=False)
        # Must not raise even though nothing is configured — the no-op path.
        cl._notify_owner("P2", "title", "body", "dedupe-key")


class TestCadenceReport:
    def test_flags_planted_over_threshold_day(self, tmp_path):
        ledger_path = tmp_path / "ledger.jsonl"
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"date": "2026-07-01", "usd": 500.0, "session_count": 3}) + "\n")
            f.write(json.dumps({"date": "2026-07-02", "usd": 2.0, "session_count": 1}) + "\n")

        report = cl.cadence_report(ledger_path=ledger_path, config=CONFIG)
        assert "2026-07-01" in report
        assert "FLAG" in report
        assert "500.00" in report

    def test_notes_gh_cron_zero_cost(self, tmp_path):
        ledger_path = tmp_path / "ledger.jsonl"
        report = cl.cadence_report(ledger_path=ledger_path, config=CONFIG)
        assert "cost $0 Claude tokens" in report
        assert "standing-goals.yml" in report


class TestReport:
    def test_report_includes_trend_and_models(self, tmp_path):
        ledger_path = tmp_path / "ledger.jsonl"
        with open(ledger_path, "w", encoding="utf-8") as f:
            for i, usd in enumerate([1.0, 2.0, 10.0, 20.0]):
                day = (date(2026, 7, 1) + timedelta(days=i)).isoformat()
                f.write(
                    json.dumps(
                        {
                            "date": day,
                            "usd": usd,
                            "tokens": {"input": 1000, "output": 500, "cache_write": 0, "cache_read": 0},
                            "by_model": {"claude-sonnet-4": {"usd": usd, "input": 1000, "output": 500, "cache_write": 0, "cache_read": 0}},
                            "by_attribution": {"main": {"usd": usd, "input": 1000, "output": 500, "cache_write": 0, "cache_read": 0}},
                            "session_count": 1,
                        }
                    )
                    + "\n"
                )
        report = cl.format_report(cl.load_ledger(ledger_path), days=4)
        assert "Total: $33.00" in report
        assert "claude-sonnet-4" in report
        assert "Trend:" in report

    def test_report_empty_ledger(self):
        assert "No ledger entries" in cl.format_report([], days=7)


class TestModelFamilyRates:
    def test_matches_family_by_substring(self):
        assert cl.model_family_rates("claude-opus-4-8", CONFIG) == CONFIG["families"]["opus"]
        assert cl.model_family_rates("claude-sonnet-4-5", CONFIG) == CONFIG["families"]["sonnet"]
        assert cl.model_family_rates("claude-haiku-3-5", CONFIG) == CONFIG["families"]["haiku"]

    def test_unknown_model_uses_default(self):
        assert cl.model_family_rates("something-else", CONFIG) == CONFIG["families"]["default"]
