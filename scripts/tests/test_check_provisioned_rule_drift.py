"""Fixture tests for the provisioned-rule drift report (T-401, + T-401 review fixes).

Classification tests are pure (no git, no disk) via an injected history/deletion list.
Repo-scan tests build a tiny fake settings.json + registry.json + repo tree under tmp_path
and drive build_report() end-to-end with injected providers, so a fake hub with real git
history never has to be constructed.
"""

import json
from datetime import datetime, timedelta, timezone

from scripts.check_provisioned_rule_drift import (
    DELETION_CHECK_FAILED,
    _cache_is_fresh,
    _write_cache,
    build_report,
    classify_rule_copy,
    render_text,
)
from scripts.dedup_check import hash_content

HUB_CURRENT = "# workflow\ncurrent hub content\n"
HUB_CURRENT_HASH = hash_content(HUB_CURRENT)

OLD_V2 = "# workflow\nold v2 content (pre-fix)\n"       # matches project copy #2
OLD_V1 = "# workflow\nold v1 content (oldest)\n"        # matches project copy #1

# Newest-first, entry 0 = the commit that produced HUB_CURRENT (same shape as
# get_hub_rule_history()'s real git-log output).
HISTORY_NEWEST_FIRST = [
    ("sha-head", "2026-07-03", "fix(P1 batch): resolve audit issues #281 (#294)", HUB_CURRENT),
    ("sha-v2", "2026-04-22", "chore(rules): strengthen verification rules", OLD_V2),
    ("sha-v1", "2026-03-10", "feat: seed patterns from KKB project", OLD_V1),
]


class TestClassifyRuleCopy:
    def test_current_when_hash_matches_hub_current(self):
        result = classify_rule_copy(HUB_CURRENT, HUB_CURRENT_HASH, HISTORY_NEWEST_FIRST)
        assert result["status"] == "CURRENT"

    def test_stale_when_hash_matches_an_older_hub_version(self):
        result = classify_rule_copy(OLD_V2, HUB_CURRENT_HASH, HISTORY_NEWEST_FIRST)
        assert result["status"] == "STALE"
        assert result["hub_commit_sha"] == "sha-v2"
        assert result["hub_commit_date"] == "2026-04-22"

    def test_stale_flags_contradiction_when_the_superseding_commit_says_fix_or_resolve(self):
        # OLD_V2 was superseded by sha-head, whose message contains "resolve" -> flagged.
        result = classify_rule_copy(OLD_V2, HUB_CURRENT_HASH, HISTORY_NEWEST_FIRST)
        assert result["contradiction"] is True
        assert result["changed_by_sha"] == "sha-head"

    def test_stale_flags_contradiction_from_ANY_later_fix_commit_not_just_the_next_one(self):
        # OLD_V1's immediately-next commit (sha-v2) is a routine "strengthen" chore, but a
        # LATER commit (sha-head) reads as a fix -> still a contradiction candidate. This is
        # the KKB/algochanakya live case: their workflow.md copy matches the 2026-04-01
        # commit, two commits before the 2026-07-03 "resolve audit issues" fix, not the one
        # immediately after it.
        result = classify_rule_copy(OLD_V1, HUB_CURRENT_HASH, HISTORY_NEWEST_FIRST)
        assert result["status"] == "STALE"
        assert result["contradiction"] is True
        assert result["changed_by_sha"] == "sha-head"

    def test_stale_does_not_flag_contradiction_when_no_later_commit_reads_as_a_fix(self):
        routine_history = [
            ("sha-head", "2026-07-03", "chore(rules): tidy formatting", HUB_CURRENT),
            ("sha-v1", "2026-03-10", "feat: seed patterns from KKB project", OLD_V1),
        ]
        result = classify_rule_copy(OLD_V1, HUB_CURRENT_HASH, routine_history)
        assert result["status"] == "STALE"
        assert result["contradiction"] is False

    def test_modified_when_hash_matches_no_hub_version(self):
        result = classify_rule_copy(
            "# workflow\ntotally custom project content\n", HUB_CURRENT_HASH, HISTORY_NEWEST_FIRST
        )
        assert result["status"] == "MODIFIED"

    def test_modified_when_history_is_an_empty_list(self):
        # Empty list = "checked, hub never had any older version" (a real, if unusual, answer).
        result = classify_rule_copy("# workflow\ncustom\n", HUB_CURRENT_HASH, [])
        assert result["status"] == "MODIFIED"

    def test_unknown_when_history_is_none(self):
        # RED->GREEN (review finding 3): history=None used to silently fall through to
        # MODIFIED, indistinguishable from "checked, no match". It must say UNKNOWN instead.
        result = classify_rule_copy("# workflow\ncustom\n", HUB_CURRENT_HASH, None)
        assert result["status"] == "UNKNOWN"
        assert "note" in result


class TestContradictionRegexWordBoundary:
    """RED->GREEN (review finding 5): the bare fix|contradict|resolve alternation matched
    substrings inside unrelated words ('suffix', 'fixture') -> false-positive contradiction
    flags. \\b keeps it to whole words."""

    def _history_with_superseding_message(self, msg):
        return [
            ("sha-head", "2026-07-03", msg, HUB_CURRENT),
            ("sha-v1", "2026-03-10", "feat: seed patterns from KKB project", OLD_V1),
        ]

    def test_true_case_whole_word_fix_flags_contradiction(self):
        history = self._history_with_superseding_message("fix(P1): resolve audit issues")
        result = classify_rule_copy(OLD_V1, HUB_CURRENT_HASH, history)
        assert result["contradiction"] is True

    def test_false_case_suffix_and_fixture_do_not_flag_contradiction(self):
        # Live false positive named by the reviewer: commit dafd04c4 "add -agent suffix".
        history = self._history_with_superseding_message("refactor: add -agent suffix, update fixture data")
        result = classify_rule_copy(OLD_V1, HUB_CURRENT_HASH, history)
        assert result["contradiction"] is False


class TestBuildReportRedGreen(object):
    """RED->GREEN: before the wiring below existed, none of this classified correctly."""

    def _write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _registry(self, tmp_path):
        registry = {
            "workflow": {"type": "rule", "hash": HUB_CURRENT_HASH},
        }
        reg_path = tmp_path / "hub" / "registry" / "patterns.json"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(json.dumps(registry), encoding="utf-8")
        return reg_path

    def _history_provider(self, filename):
        assert filename == "workflow.md"
        return HISTORY_NEWEST_FIRST

    def _no_deletion(self, filename):
        return None

    def _no_git_state(self, repo_path):
        return None

    def test_repo_with_current_copy_classifies_current(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_a = tmp_path / "repo-a"
        self._write(repo_a / ".claude" / "rules" / "workflow.md", HUB_CURRENT)

        settings = {"repo_registry": {"repo-a": {"path": str(repo_a)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=self._history_provider,
            deletion_provider=self._no_deletion,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert rows == [{"file": "workflow.md", "status": "CURRENT"}]

    def test_repo_with_stale_pre_fix_copy_classifies_stale_and_contradiction(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_b = tmp_path / "repo-b"
        self._write(repo_b / ".claude" / "rules" / "workflow.md", OLD_V2)

        settings = {"repo_registry": {"repo-b": {"path": str(repo_b)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=self._history_provider,
            deletion_provider=self._no_deletion,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["status"] == "STALE"
        assert rows[0]["contradiction"] is True

        stale_count, repos_with_stale = 1, 1
        # cross-check against the module's own summarizer via render_text's summary line
        from scripts.check_provisioned_rule_drift import _summarize
        assert _summarize(report) == (stale_count, repos_with_stale)

    def test_repo_with_customized_copy_classifies_modified(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_c = tmp_path / "repo-c"
        self._write(repo_c / ".claude" / "rules" / "workflow.md", "# workflow\nproject-specific rewrite\n")

        settings = {"repo_registry": {"repo-c": {"path": str(repo_c)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=self._history_provider,
            deletion_provider=self._no_deletion,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert rows[0]["status"] == "MODIFIED"

    def test_repo_with_project_only_file_has_no_hub_twin_and_no_deletion(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_d = tmp_path / "repo-d"
        self._write(repo_d / ".claude" / "rules" / "project-only-rule.md", "# something local\n")

        settings = {"repo_registry": {"repo-d": {"path": str(repo_d)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=lambda filename: None,
            deletion_provider=self._no_deletion,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert rows == [{"file": "project-only-rule.md", "status": "PROJECT-ONLY"}]

    def test_repo_with_retired_file_classifies_retired_not_project_only(self, tmp_path):
        # RED->GREEN (review finding 2): before this, a project enforcing a rule the hub
        # deleted was indistinguishable from a harmless project-local rule (both
        # PROJECT-ONLY). Live check: prompt-auto-enhance-rule.md, deleted in hub commit
        # 386aeae9 (#199), must show RETIRED in every repo that still carries it.
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_r = tmp_path / "repo-r"
        self._write(repo_r / ".claude" / "rules" / "prompt-auto-enhance-rule.md", "# retired rule, still enforced\n")

        settings = {"repo_registry": {"repo-r": {"path": str(repo_r)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        def deletion_provider(filename):
            assert filename == "prompt-auto-enhance-rule.md"
            return ("386aeae9f1893fae449d9a748e1a04a34e0a0d3e", "2026-06-23", "feat(agent-teams): incorporate + live-validate Claude Code agent teams; hub refinements (#199)")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=lambda filename: None,
            deletion_provider=deletion_provider,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["status"] == "RETIRED"
        assert "386aeae9" in rows[0]["note"]
        assert "2026-06-23" in rows[0]["note"]

    def test_repo_with_deletion_check_failure_becomes_a_note_not_a_silent_project_only(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_f = tmp_path / "repo-f"
        self._write(repo_f / ".claude" / "rules" / "project-only-rule.md", "# something local\n")

        settings = {"repo_registry": {"repo-f": {"path": str(repo_f)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=lambda filename: None,
            deletion_provider=lambda filename: DELETION_CHECK_FAILED,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert rows[0]["status"] == "NOTE"
        assert "could not check" in rows[0]["note"]

    def test_missing_repo_path_is_a_note_never_a_silent_zero(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        settings = {"repo_registry": {"ghost-repo": {"path": str(tmp_path / "does-not-exist")}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=lambda filename: None,
        )
        assert report["repos"][0]["rows"] == []
        assert "path not found" in report["repos"][0]["note"]
        assert any("ghost-repo" in note for note in report["notes"])

    def test_missing_settings_file_is_a_note_never_a_crash(self, tmp_path):
        report = build_report(
            settings_path=tmp_path / "no-such-settings.json",
            hub_root=tmp_path / "hub",
        )
        assert report["repos"] == []
        assert any("not found" in note or "unreadable" in note for note in report["notes"])

    def test_underscore_doc_key_in_repo_registry_is_skipped(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        settings = {"repo_registry": {"_doc": "explanatory text, not a repo"}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(settings_path=settings_path, hub_root=hub_root, history_provider=lambda f: None)
        assert report["repos"] == []

    def test_unreadable_file_becomes_a_note_row(self, tmp_path):
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_e = tmp_path / "repo-e"
        rule_file = repo_e / ".claude" / "rules" / "workflow.md"
        rule_file.parent.mkdir(parents=True, exist_ok=True)
        # Write bytes that are not valid UTF-8 to force a UnicodeDecodeError on read.
        rule_file.write_bytes(b"\xff\xfe\x00\x01broken")

        settings = {"repo_registry": {"repo-e": {"path": str(repo_e)}}}
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=self._history_provider,
            deletion_provider=self._no_deletion,
            git_state_provider=self._no_git_state,
        )
        rows = report["repos"][0]["rows"]
        assert rows[0]["status"] == "NOTE"
        assert "unreadable" in rows[0]["note"]

    def test_scan_deadline_skips_remaining_repos_with_a_named_note(self, tmp_path):
        # RED->GREEN (review finding 4): an unbounded scan over a huge repo_registry (or one
        # stuck talking to a slow/hung git process) must degrade to a NOTE naming what was
        # skipped, never hang the caller. A deadline of 0 seconds in the past guarantees every
        # repo after the first check is skipped.
        hub_root = tmp_path / "hub"
        self._registry(tmp_path)
        repo_a = tmp_path / "repo-a"
        self._write(repo_a / ".claude" / "rules" / "workflow.md", HUB_CURRENT)
        repo_b = tmp_path / "repo-b"
        self._write(repo_b / ".claude" / "rules" / "workflow.md", HUB_CURRENT)

        settings = {
            "repo_registry": {
                "repo-a": {"path": str(repo_a)},
                "repo-b": {"path": str(repo_b)},
            }
        }
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        report = build_report(
            settings_path=settings_path,
            hub_root=hub_root,
            history_provider=self._history_provider,
            deletion_provider=self._no_deletion,
            git_state_provider=self._no_git_state,
            deadline_seconds=-1,  # already expired before the loop even starts
        )
        assert report["repos"] == []
        assert any("skipped repos" in note and "repo-a" in note and "repo-b" in note for note in report["notes"])


class TestRenderTextPrintsNotes:
    """RED->GREEN (review finding 3): render_text used to only print the `note` field for
    NOTE-status rows, dropping it for every other status (e.g. UNKNOWN, RETIRED)."""

    def _report(self, rows):
        return {
            "repos": [{"repo": "some-repo", "rows": rows, "note": None, "git_state": None}],
            "notes": [],
            "history_cap": 30,
        }

    def test_note_field_is_printed_for_a_non_note_status_row(self):
        report = self._report([
            {"file": "some-rule.md", "status": "UNKNOWN", "note": "hub git history unavailable for this file"},
        ])
        text = render_text(report)
        assert "some-rule.md" in text
        assert "hub git history unavailable for this file" in text

    def test_note_field_is_printed_for_a_retired_row(self):
        report = self._report([
            {"file": "old-rule.md", "status": "RETIRED", "note": "hub deleted it on 2026-06-23 (386aeae9f1): feat(...)"},
        ])
        text = render_text(report)
        assert "hub deleted it on 2026-06-23" in text

    def test_git_state_header_line_is_rendered(self):
        report = {
            "repos": [{
                "repo": "IPODhan",
                "rows": [],
                "note": None,
                "git_state": {
                    "branch": "audit/skyways-field-audit",
                    "upstream": "origin/main",
                    "ahead": 2,
                    "behind": 0,
                    "default_branch": "main",
                    "notes": ["not on default branch (default=main)"],
                },
            }],
            "notes": [],
            "history_cap": 30,
        }
        text = render_text(report)
        assert "read: working tree @ audit/skyways-field-audit (ahead 2 / behind 0 of origin/main)" in text
        assert "not on default branch (default=main)" in text


class TestCache:
    def test_cache_is_fresh_for_a_run_from_moments_ago(self, tmp_path):
        cache_path = tmp_path / "rule-drift" / ".last-run.json"
        _write_cache(cache_path, "rule-drift: 3 stale across 2 repos")
        assert _cache_is_fresh(cache_path) is True

    def test_cache_is_stale_after_more_than_seven_days(self, tmp_path):
        cache_path = tmp_path / "rule-drift" / ".last-run.json"
        old = datetime.now(timezone.utc) - timedelta(days=8)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"run_at": old.isoformat(), "summary": "old"}), encoding="utf-8")
        assert _cache_is_fresh(cache_path) is False

    def test_cache_is_not_fresh_when_file_is_missing(self, tmp_path):
        assert _cache_is_fresh(tmp_path / "rule-drift" / "does-not-exist.json") is False

    def test_cache_is_not_fresh_when_file_is_malformed_json(self, tmp_path):
        cache_path = tmp_path / "rule-drift" / ".last-run.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("{not valid json", encoding="utf-8")
        assert _cache_is_fresh(cache_path) is False

    def test_cache_is_not_fresh_when_run_at_key_is_missing(self, tmp_path):
        cache_path = tmp_path / "rule-drift" / ".last-run.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"summary": "no timestamp"}), encoding="utf-8")
        assert _cache_is_fresh(cache_path) is False

    def test_cache_is_not_fresh_when_run_at_is_unparseable(self, tmp_path):
        cache_path = tmp_path / "rule-drift" / ".last-run.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"run_at": "not-a-timestamp", "summary": "x"}), encoding="utf-8")
        assert _cache_is_fresh(cache_path) is False

    def test_write_cache_round_trips_through_cache_is_fresh(self, tmp_path):
        cache_path = tmp_path / "rule-drift" / ".last-run.json"
        _write_cache(cache_path, "rule-drift: 0 stale across 5 repos")
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        assert cached["summary"] == "rule-drift: 0 stale across 5 repos"
        assert _cache_is_fresh(cache_path) is True
