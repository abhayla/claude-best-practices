"""Hand-computable tests for the feature-utilization meter.

Every fixture below is small enough to add up by eye: 2 owner sessions + 1 fleet-worker
session + 1 subagent transcript (carrying its PARENT session's id, as real ones do), and a
fake home with 2 user skills, 1 user agent and a multi-version, multi-marketplace plugin.
The assertions are the numbers a human gets counting the fixture lines.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts import feature_utilization as fu

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
RECENT = (NOW - timedelta(days=2)).isoformat().replace("+00:00", "Z")
OLD = (NOW - timedelta(days=90)).isoformat().replace("+00:00", "Z")


def assistant(session, timestamp, model, tools=()):
    content = [{"type": "tool_use", "id": "t", "name": name, "input": ti} for name, ti in tools]
    return {
        "type": "assistant",
        "sessionId": session,
        "timestamp": timestamp,
        "message": {"role": "assistant", "model": model, "content": content},
    }


def user_slash(session, timestamp, command, with_body=True):
    """A slash command as older Claude Code records it: a marker entry plus a marker-less
    body entry. Only the marker carries <command-name>, so a correct counter sees ONE."""
    entries = [
        {
            "type": "user",
            "sessionId": session,
            "timestamp": timestamp,
            "message": {
                "role": "user",
                "content": (
                    f"<command-message>{command}</command-message>\n"
                    f"<command-name>/{command}</command-name>\n<command-args></command-args>"
                ),
            },
        }
    ]
    if with_body:
        entries.append(
            {
                "type": "user",
                "sessionId": session,
                "timestamp": timestamp,
                "message": {"role": "user", "content": f"body of {command}, no marker here"},
            }
        )
    return entries


def system_slash(session, timestamp, command):
    """The shape newer CLI versions use: ONE system/local_command entry, no body twin."""
    return {
        "type": "system",
        "subtype": "local_command",
        "sessionId": session,
        "timestamp": timestamp,
        "content": (
            f"<command-name>/{command}</command-name>\n"
            f"            <command-message>{command}</command-message>\n"
            f"            <command-args></command-args>"
        ),
    }


def write_jsonl(path: Path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


@pytest.fixture
def projects_dir(tmp_path):
    root = tmp_path / "projects"
    owner = root / "D--Abhay-Ventures-demo"
    fleet = root / "D--Abhay-GetWorkDone-workspaces-cbp-T999"

    # Owner session 1: plan mode (ExitPlanMode), a worktree, an Agent (sonnet), a slash
    # command, a CLI built-in, and an OLD entry that must fall outside a 30-day window.
    write_jsonl(
        owner / "sess-1.jsonl",
        [
            assistant("sess-1", RECENT, "claude-opus-5", [("ExitPlanMode", {})]),
            assistant("sess-1", RECENT, "claude-opus-5", [("EnterWorktree", {})]),
            assistant(
                "sess-1",
                RECENT,
                "claude-opus-5",
                [("Agent", {"subagent_type": "code-reviewer-agent", "model": "sonnet"})],
            ),
            *user_slash("sess-1", RECENT, "get-work-done"),
            system_slash("sess-1", RECENT, "clear"),
            assistant("sess-1", OLD, "claude-opus-5", [("WebSearch", {})]),
            *user_slash("sess-1", OLD, "brainstorm"),
        ],
    )

    # Owner session 2: a Skill tool call, an MCP call, a second Agent on opus, plus one
    # genuinely corrupt line (a truncated write) that must be counted and skipped.
    write_jsonl(
        owner / "sess-2.jsonl",
        [
            assistant("sess-2", RECENT, "claude-sonnet-5", [("Skill", {"skill": "demo-plugin:helper"})]),
            assistant("sess-2", RECENT, "claude-sonnet-5", [("mcp__playwright__browser_click", {})]),
            assistant(
                "sess-2",
                RECENT,
                "claude-sonnet-5",
                [("Agent", {"subagent_type": "code-reviewer-agent", "model": "opus"})],
            ),
        ],
    )
    with open(owner / "sess-2.jsonl", "a", encoding="utf-8") as f:
        f.write('{"type": "assistant", "message": {"content": [{"type": "tool_use"\n')

    # Subagent transcript of owner session 2 — real ones carry the PARENT sessionId.
    write_jsonl(
        owner / "sess-2" / "subagents" / "agent-abc.jsonl",
        [
            assistant("sess-2", RECENT, "claude-sonnet-5", [("Bash", {})]),
            assistant("sess-2", RECENT, "claude-sonnet-5", [("ToolSearch", {})]),
            *user_slash("sess-2", RECENT, "should-not-count", with_body=False),
        ],
    )

    # Fleet worker: an Agent on haiku plus a slash command — must land in the fleet bucket.
    write_jsonl(
        fleet / "sess-fleet.jsonl",
        [
            assistant(
                "sess-fleet",
                RECENT,
                "claude-haiku-5",
                [("Agent", {"subagent_type": "general-purpose", "model": "haiku"})],
            ),
            assistant("sess-fleet", RECENT, "claude-haiku-5", [("Monitor", {})]),
            *user_slash("sess-fleet", RECENT, "get-work-done"),
        ],
    )
    return root


@pytest.fixture
def fake_home(tmp_path):
    home = tmp_path / "home"
    skills = home / ".claude" / "skills"
    for name in ("get-work-done", "never-touched-skill"):
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text("# skill", encoding="utf-8")
    agents = home / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "never-touched-agent.md").write_text("# agent", encoding="utf-8")

    cache = home / ".claude" / "plugins" / "cache"
    market = cache / "market"
    for version in ("0.1.0", "0.2.0"):
        skill_dir = market / "demo-plugin" / version / "skills" / "helper"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# helper", encoding="utf-8")
    # Only the newest version carries this skill — proving the highest-version pick.
    extra = market / "demo-plugin" / "0.2.0" / "skills" / "newer-only"
    extra.mkdir(parents=True)
    (extra / "SKILL.md").write_text("# newer", encoding="utf-8")
    # A stale git-hash checkout must NOT outrank 0.2.0.
    hashed = market / "demo-plugin" / "614b4ebe2319" / "skills" / "stale-only"
    hashed.mkdir(parents=True)
    (hashed / "SKILL.md").write_text("# stale", encoding="utf-8")
    # The SAME plugin name under a second marketplace must survive.
    other = cache / "official" / "demo-plugin" / "1.0.0" / "skills" / "official-only"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("# official", encoding="utf-8")
    # A second plugin that also ships a skill named `helper` — makes a bare `helper`
    # observation ambiguous.
    twin = cache / "official" / "twin-plugin" / "1.0.0" / "skills" / "helper"
    twin.mkdir(parents=True)
    (twin / "SKILL.md").write_text("# twin helper", encoding="utf-8")
    # A temp git marketplace must be ignored entirely.
    junk = cache / "temp_git_123" / "junk" / "9.9.9" / "skills" / "junk-skill"
    junk.mkdir(parents=True)
    (junk / "SKILL.md").write_text("# junk", encoding="utf-8")

    # Only these three cached plugins are actually ENABLED (Claude Code only loads what
    # settings.json lists) — every fixture plugin above must be listed here or it silently
    # drops out of every existing coverage/inventory assertion below.
    (home / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "enabledPlugins": {
                    "demo-plugin@market": True,
                    "demo-plugin@official": True,
                    "twin-plugin@official": True,
                }
            }
        ),
        encoding="utf-8",
    )
    return home


# --------------------------------------------------------------------------------------
# Window / bucketing / counting
# --------------------------------------------------------------------------------------


def test_window_filters_out_old_entries(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    assert usage["tool_calls"]["owner"]["WebSearch"] == 0
    assert "brainstorm" not in usage["slash_calls"]
    assert usage["tool_calls"]["owner"]["ExitPlanMode"] == 1

    wide = fu.scan_usage(projects_dir, days=365, now=NOW)
    assert wide["tool_calls"]["owner"]["WebSearch"] == 1
    assert wide["slash_calls"]["brainstorm"] == 1


def test_slash_marker_counted_once_and_subagent_markers_ignored(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    # One owner marker + one fleet marker = 2 total, 1 attributed to the owner.
    assert usage["slash_calls"]["get-work-done"] == 2
    assert usage["slash_owner"]["get-work-done"] == 1
    assert "should-not-count" not in usage["slash_calls"]


def test_system_local_command_slash_counted_once(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    assert usage["slash_calls"]["clear"] == 1


def test_three_buckets_split_owner_subagent_and_fleet(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    # Subagent tool calls must NOT inflate the owner's own calls.
    assert usage["tool_calls"]["owner"]["ToolSearch"] == 0
    assert usage["tool_calls"]["owner-subagent"]["ToolSearch"] == 1
    assert usage["tool_calls"]["owner-subagent"]["Bash"] == 1
    assert usage["tool_calls"]["fleet-workers"]["Monitor"] == 1
    assert usage["tool_calls"]["owner"]["Monitor"] == 0
    # Sessions stay parent-based: the subagent shares sess-2's id.
    assert usage["sessions"]["owner"] == {"sess-1", "sess-2"}
    assert usage["sessions"]["owner-subagent"] == {"sess-2"}
    assert usage["sessions"]["fleet-workers"] == {"sess-fleet"}
    assert usage["projects"] == {"Abhay-Ventures-demo": 2}
    assert usage["models"]["fleet-workers"] == {"claude-haiku-5": 2}
    assert usage["models"]["owner-subagent"] == {"claude-sonnet-5": 2}


def test_fleet_slug_markers():
    assert fu.project_bucket("D--Abhay-GetWorkDone-workspaces-x") == "fleet-workers"
    assert fu.project_bucket("C--Users-itsab-AppData-Local-Temp-abc") == "fleet-workers"
    assert fu.project_bucket("D--Abhay-GetWorkDone-wt-check-cbp-feature-meter") == "fleet-workers"
    assert fu.project_bucket("D--repo-worktrees-thing") == "fleet-workers"
    assert fu.project_bucket("D--repo-wt-thing") == "fleet-workers"
    assert fu.project_bucket("D--Abhay-Ventures-demo") == "Abhay-Ventures-demo"


def test_agents_counted_by_type_model_and_bucket(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    assert usage["agents"][("code-reviewer-agent", "sonnet", "owner")] == 1
    assert usage["agents"][("code-reviewer-agent", "opus", "owner")] == 1
    assert usage["agents"][("general-purpose", "haiku", "fleet-workers")] == 1


def test_mcp_calls_attributed_to_server(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    assert usage["mcp_calls"]["owner"]["playwright"] == 1
    assert usage["tool_calls"]["owner"]["mcp"] == 1


def test_malformed_line_counted_only_on_decode_error(projects_dir):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    assert usage["stats"]["lines_malformed"] == 1  # the truncated line, nothing else
    assert usage["stats"]["files_scanned"] == 4
    assert usage["stats"]["subagent_files_scanned"] == 1


def test_decode_line_distinguishes_junk_from_uninteresting():
    assert fu.decode_line("") == (None, True)          # blank is not corruption
    assert fu.decode_line("{not json")[1] is False     # this is
    entry, ok = fu.decode_line('{"type": "user", "message": {"content": "hi"}}')
    assert ok and entry["type"] == "user"
    assert fu.parse_line('{"type": "user", "message": {"content": "hi"}}') is None


def test_old_files_are_skipped_by_mtime(projects_dir):
    """A transcript last written before the window cannot hold an in-window entry — the
    whole-file skip is what keeps a real multi-GB scan cheap."""
    import os

    stale = projects_dir / "D--Abhay-Ventures-demo" / "sess-1.jsonl"
    old_epoch = (NOW - timedelta(days=200)).timestamp()
    os.utime(stale, (old_epoch, old_epoch))

    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    assert usage["stats"]["files_scanned"] == 3
    assert usage["tool_calls"]["owner"]["ExitPlanMode"] == 0


def test_unreadable_projects_dir_is_a_note_not_a_silent_zero(tmp_path):
    usage = fu.scan_usage(tmp_path / "does-not-exist", days=30, now=NOW)
    assert usage["stats"]["files_scanned"] == 0
    assert any("transcripts dir not found" in note for note in usage["notes"])


# --------------------------------------------------------------------------------------
# Version ordering / inventory
# --------------------------------------------------------------------------------------


def test_version_key_orders_semver_above_hashes_and_prereleases_below_releases():
    assert fu._version_key("0.2.0") > fu._version_key("614b4ebe2319")
    assert fu._version_key("0.1.0") > fu._version_key("unknown")
    assert fu._version_key("0.10.0") > fu._version_key("0.9.0")
    assert fu._version_key("1.0.0") > fu._version_key("1.0.0-beta")
    assert fu._version_key("1.0.0-beta.2") > fu._version_key("1.0.0-beta.1")
    # Among hash-named dirs the newest on disk wins — the only signal a hash carries.
    assert fu._version_key("aaaa", mtime=200.0) > fu._version_key("bbbb", mtime=100.0)


def test_declared_plugin_version_beats_a_hash_directory_name(tmp_path):
    cache = tmp_path / "cache" / "market" / "p"
    hashed = cache / "614b4ebe2319"
    (hashed / ".claude-plugin").mkdir(parents=True)
    (hashed / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "p", "version": "9.9.9"}), encoding="utf-8"
    )
    (hashed / "skills" / "from-hash-dir").mkdir(parents=True)
    (hashed / "skills" / "from-hash-dir" / "SKILL.md").write_text("x", encoding="utf-8")
    older = cache / "1.0.0" / "skills" / "from-semver-dir"
    older.mkdir(parents=True)
    (older / "SKILL.md").write_text("x", encoding="utf-8")

    picked = fu.plugin_versions(tmp_path / "cache")
    assert picked[("market", "p")] == hashed


def test_plugin_inventory_highest_version_both_marketplaces_no_temp(fake_home):
    inventory = fu.build_inventory(repos=[], home=fake_home)
    assert inventory["plugins"] == [
        "market/demo-plugin",
        "official/demo-plugin",
        "official/twin-plugin",
    ]
    assert "demo-plugin:helper" in inventory["skills"]
    assert "demo-plugin:newer-only" in inventory["skills"]
    assert "demo-plugin:stale-only" not in inventory["skills"]      # hash dir lost, correctly
    assert "demo-plugin:official-only" in inventory["skills"]       # second marketplace kept
    assert not any(name.startswith("junk") for name in inventory["skills"])


def test_missing_plugin_cache_is_a_note(tmp_path):
    inventory = fu.build_inventory(repos=[], home=tmp_path / "empty-home")
    assert any("plugin cache not found" in note for note in inventory["notes"])
    assert any("user config dir not found" in note for note in inventory["notes"])


def test_repo_skills_and_agents_are_inventoried(tmp_path, fake_home):
    repo = tmp_path / "myrepo"
    (repo / ".claude" / "skills" / "repo-skill").mkdir(parents=True)
    (repo / ".claude" / "skills" / "repo-skill" / "SKILL.md").write_text("x", encoding="utf-8")
    (repo / ".claude" / "agents").mkdir(parents=True)
    (repo / ".claude" / "agents" / "repo-agent.md").write_text("x", encoding="utf-8")

    inventory = fu.build_inventory(repos=[repo], home=fake_home)
    assert inventory["skills"]["repo-skill"] == "repo:myrepo"
    assert inventory["agents"]["repo-agent"] == "repo:myrepo"


# --------------------------------------------------------------------------------------
# Enabled vs cached-but-not-enabled plugins (T-395)
# --------------------------------------------------------------------------------------


@pytest.fixture
def enablement_home(tmp_path):
    """One cached plugin ENABLED in settings.json, one cached but NEVER enabled anywhere —
    the exact shape that tripped the real report (cbp-* plugins cached, none enabled)."""
    home = tmp_path / "home2"
    cache = home / ".claude" / "plugins" / "cache" / "mkt"

    on_skill = cache / "on-plugin" / "1.0.0" / "skills" / "on-skill"
    on_skill.mkdir(parents=True)
    (on_skill / "SKILL.md").write_text("# on", encoding="utf-8")

    off_skill = cache / "off-plugin" / "1.0.0" / "skills" / "off-skill"
    off_skill.mkdir(parents=True)
    (off_skill / "SKILL.md").write_text("# off", encoding="utf-8")
    off_agent = cache / "off-plugin" / "1.0.0" / "agents"
    off_agent.mkdir(parents=True)
    (off_agent / "off-agent.md").write_text("# off agent", encoding="utf-8")

    (home / ".claude").mkdir(parents=True, exist_ok=True)
    (home / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {"on-plugin@mkt": True}}), encoding="utf-8"
    )
    return home


def test_cached_but_not_enabled_plugin_excluded_from_inventory_and_coverage(enablement_home):
    inventory = fu.build_inventory(repos=[], home=enablement_home)

    # Still visible in the raw cached-plugin list...
    assert inventory["plugins"] == ["mkt/off-plugin", "mkt/on-plugin"]
    # ...but the disabled plugin's skill/agent must NOT be counted as installed/available.
    assert "on-plugin:on-skill" in inventory["skills"]
    assert "off-plugin:off-skill" not in inventory["skills"]
    assert "off-plugin:off-agent" not in inventory["agents"]

    assert inventory["enabled_plugins"] == ["mkt/on-plugin"]
    assert inventory["not_enabled_plugins"] == [
        {"plugin": "mkt/off-plugin", "skills": 1, "agents": 1}
    ]

    empty_usage = fu.scan_usage(enablement_home, days=30, now=NOW)  # no transcripts here
    report = fu.build_report(
        empty_usage, inventory, {"servers": [], "notes": []}, {}, days=30
    )

    # Coverage denominator counts ONLY the enabled plugin's skill.
    assert report["skills"]["available_total"] == 1
    assert report["coverage"]["skills_available"] == 1
    # The disabled plugin's skill must not appear in "available but never used" either —
    # it was never counted as available in the first place.
    assert "off-plugin:off-skill" not in report["skills"]["never_used"]
    assert report["plugins_enabled"] == ["mkt/on-plugin"]
    assert report["plugins_not_enabled"] == [
        {"plugin": "mkt/off-plugin", "skills": 1, "agents": 1}
    ]


def test_load_enabled_plugins_merges_scopes_later_wins(tmp_path):
    user_settings = tmp_path / "user-settings.json"
    user_settings.write_text(
        json.dumps({"enabledPlugins": {"a@mkt": True, "b@mkt": True}}), encoding="utf-8"
    )
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {"b@mkt": False}}), encoding="utf-8"
    )

    merged = fu.load_enabled_plugins(user_settings, [repo])
    assert merged == {"a@mkt": True, "b@mkt": False}


def test_missing_user_settings_file_is_a_note_not_a_crash(tmp_path):
    notes: list = []
    merged = fu.load_enabled_plugins(tmp_path / "does-not-exist.json", [], notes=notes)
    assert merged == {}
    assert any("enablement scope" in note and "missing" in note for note in notes)


def test_load_enabled_plugins_settings_local_overrides_project_settings(tmp_path):
    """Third scope: settings.local.json must win over settings.json for the SAME repo -- if
    the merge order were reversed this would assert True instead of False (T-395 review
    finding 6)."""
    user_settings = tmp_path / "user-settings.json"
    user_settings.write_text(json.dumps({"enabledPlugins": {}}), encoding="utf-8")
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {"a@mkt": True}}), encoding="utf-8"
    )
    (repo / ".claude" / "settings.local.json").write_text(
        json.dumps({"enabledPlugins": {"a@mkt": False}}), encoding="utf-8"
    )

    merged = fu.load_enabled_plugins(user_settings, [repo])
    assert merged == {"a@mkt": False}


def test_truthy_non_true_value_does_not_enable_a_plugin(tmp_path):
    """1 and "true" are truthy in Python but are NOT the boolean true settings.json actually
    writes -- only `is True` may enable a plugin (T-395 review finding 6)."""
    home = tmp_path / "home-truthy"
    cache = home / ".claude" / "plugins" / "cache" / "mkt"
    skill = cache / "p" / "1.0.0" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("x", encoding="utf-8")
    (home / ".claude").mkdir(parents=True, exist_ok=True)
    (home / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {"p@mkt": 1}}), encoding="utf-8"
    )

    inventory = fu.build_inventory(repos=[], home=home)
    assert inventory["enabled_plugins"] == []
    assert inventory["not_enabled_plugins"] == [{"plugin": "mkt/p", "skills": 1, "agents": 0}]


def test_enabled_plugins_key_absent_is_noted_not_silent(tmp_path):
    """A settings.json with no enabledPlugins key at all must say so, not silently read as
    {} (T-395 review finding 2)."""
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"someOtherKey": True}), encoding="utf-8")
    notes: list = []

    merged = fu.load_enabled_plugins(settings, [], notes=notes)
    assert merged == {}
    assert any("no enabledPlugins map (key absent)" in note for note in notes)


def test_enabled_plugins_wrong_type_is_noted_not_silent(tmp_path):
    """enabledPlugins present but not a dict (e.g. a list) must say so, not silently read as
    {} (T-395 review finding 2)."""
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"enabledPlugins": ["a@mkt"]}), encoding="utf-8")
    notes: list = []

    merged = fu.load_enabled_plugins(settings, [], notes=notes)
    assert merged == {}
    assert any("no enabledPlugins map (wrong type: list)" in note for note in notes)


def test_enablement_scope_notes_record_path_and_entry_count(tmp_path):
    """Every scope actually read gets an 'enablement scope: <path> (N entries)' note -- this
    is what explains a coverage swing between two --repo runs (T-395 review finding 1)."""
    user_settings = tmp_path / "user-settings.json"
    user_settings.write_text(
        json.dumps({"enabledPlugins": {"a@mkt": True, "b@mkt": False}}), encoding="utf-8"
    )
    notes: list = []

    fu.load_enabled_plugins(user_settings, [], notes=notes)
    assert f"enablement scope: {user_settings} (2 entries)" in notes


def test_enabled_but_not_cached_plugin_is_noted(tmp_path):
    """A settings.json enables a plugin@marketplace with NO matching cached dir -- config
    drift that must be visible, not silently ignored (T-395 review finding 4)."""
    home = tmp_path / "home-drift"
    (home / ".claude").mkdir(parents=True, exist_ok=True)
    (home / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {"ghost-plugin@mkt": True}}), encoding="utf-8"
    )
    # No plugins/cache dir at all -- the enabled key still has no matching install.

    inventory = fu.build_inventory(repos=[], home=home)
    assert any("enabled but not cached: ghost-plugin@mkt" in note for note in inventory["notes"])


def test_user_settings_path_override_is_used_by_build_inventory(tmp_path):
    """The user_settings_path param on build_inventory is not dead -- a real caller
    (collect()/--user-settings-path, tested below) uses it, and it is exercised directly
    here (T-395 review finding 5)."""
    home = tmp_path / "home-override"
    cache = home / ".claude" / "plugins" / "cache" / "mkt"
    skill = cache / "p" / "1.0.0" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("x", encoding="utf-8")
    # Deliberately NO settings.json under home/.claude -- enablement comes only from the
    # override path elsewhere on disk.
    custom_settings = tmp_path / "elsewhere-settings.json"
    custom_settings.write_text(json.dumps({"enabledPlugins": {"p@mkt": True}}), encoding="utf-8")

    inventory = fu.build_inventory(repos=[], home=home, user_settings_path=custom_settings)
    assert inventory["enabled_plugins"] == ["mkt/p"]


def test_collect_threads_user_settings_path_override(tmp_path):
    """collect() (and therefore --user-settings-path in _main) actually plumbs the override
    down to build_inventory (T-395 review finding 5)."""
    home = tmp_path / "home-collect"
    cache = home / ".claude" / "plugins" / "cache" / "mkt"
    skill = cache / "p" / "1.0.0" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("x", encoding="utf-8")
    custom_settings = tmp_path / "elsewhere-settings.json"
    custom_settings.write_text(json.dumps({"enabledPlugins": {"p@mkt": True}}), encoding="utf-8")
    projects_dir = tmp_path / "projects-empty"
    projects_dir.mkdir()

    report = fu.collect(
        projects_dir, days=30, repos=[], home=home, now=NOW, user_settings_path=custom_settings
    )
    assert report["plugins_enabled"] == ["mkt/p"]


def test_slash_call_to_not_enabled_plugin_skill_is_not_a_cli_command(tmp_path, enablement_home):
    """A slash call matching a cached-but-not-enabled plugin's bare skill name must be
    classified as a SKILL (and land in used_not_installed, uncredited), never miscounted as
    a plain CLI built-in (T-395 review finding 3)."""
    root = tmp_path / "projects"
    write_jsonl(root / "D--demo" / "sess.jsonl", user_slash("sess", RECENT, "off-skill"))

    usage = fu.scan_usage(root, days=30, now=NOW)
    inventory = fu.build_inventory(repos=[], home=enablement_home)
    report = fu.build_report(usage, inventory, {"servers": [], "notes": []}, {}, days=30)

    assert "off-skill" not in report["cli_commands"]
    assert "off-skill" in report["skills"]["used_not_installed"]


def test_not_enabled_plugins_returned_pre_sorted_no_double_sort(enablement_home):
    """build_inventory returns not_enabled_plugins already sorted by plugin -- build_report
    must reuse it as-is (T-395 review finding 7: no duplicate sort)."""
    inventory = fu.build_inventory(repos=[], home=enablement_home)
    plugins_order = [item["plugin"] for item in inventory["not_enabled_plugins"]]
    assert plugins_order == sorted(plugins_order)


# --------------------------------------------------------------------------------------
# Credit resolution
# --------------------------------------------------------------------------------------


def test_matching_is_namespace_exact_and_ambiguity_is_not_credited():
    available = {"writing-plans", "superpowers:writing-plans", "a:helper", "b:helper", "c:solo"}

    qualified = fu.resolve_used(["superpowers:writing-plans"], available)
    assert qualified["credited"] == {"superpowers:writing-plans"}

    bare_local = fu.resolve_used(["writing-plans"], available)
    assert bare_local["credited"] == {"writing-plans"}  # local only, never the plugin twin

    ambiguous = fu.resolve_used(["helper"], available)
    assert ambiguous["credited"] == set()
    assert ambiguous["ambiguous"] == [("helper", ["a:helper", "b:helper"])]

    # A bare name matching exactly ONE plugin entry is still not credited to a guess.
    single = fu.resolve_used(["solo"], available)
    assert single["credited"] == set()
    assert single["ambiguous"] == [("solo", ["c:solo"])]

    unknown = fu.resolve_used(["not-installed", "nope:missing"], available)
    assert unknown["credited"] == set()
    assert sorted(unknown["unmatched"]) == ["nope:missing", "not-installed"]


# --------------------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------------------


def _report(projects_dir, fake_home, servers=("playwright", "hostinger-api")):
    usage = fu.scan_usage(projects_dir, days=30, now=NOW)
    inventory = fu.build_inventory(repos=[], home=fake_home)
    return fu.build_report(
        usage,
        inventory,
        {"servers": list(servers), "notes": []},
        {"/nowhere/settings.json": {"events": [], "note": "unverified — file not found"}},
        days=30,
    )


def test_slash_stream_split_into_skills_and_cli_commands(projects_dir, fake_home):
    report = _report(projects_dir, fake_home)
    assert report["cli_commands"] == {"clear": 1}
    assert [row["skill"] for row in report["skills"]["used"]] == [
        "get-work-done",
        "demo-plugin:helper",
    ]


def test_never_used_lists_and_coverage(projects_dir, fake_home):
    report = _report(projects_dir, fake_home)

    # Installed skills: get-work-done, never-touched-skill (user) + demo-plugin:helper,
    # demo-plugin:newer-only, demo-plugin:official-only, twin-plugin:helper (plugins) = 6.
    # Credited: get-work-done (bare -> local) + demo-plugin:helper (qualified) = 2.
    assert report["skills"]["available_total"] == 6
    assert report["skills"]["never_used"] == [
        "demo-plugin:newer-only",
        "demo-plugin:official-only",
        "never-touched-skill",
        "twin-plugin:helper",
    ]
    assert report["agents"]["never_used"] == ["never-touched-agent"]
    assert report["mcp"]["never_called"] == ["hostinger-api"]

    coverage = report["coverage"]
    assert coverage["skills_available"] == 6
    assert coverage["skills_used_by_owner"] == 2
    assert coverage["agents_available"] == 1
    assert coverage["agents_used_by_owner"] == 0
    assert coverage["percent_used_by_owner"] == pytest.approx(2 / 7 * 100)

    unused = report["primitives_never_used_by_owner"]
    assert "CronCreate" in unused and "Artifact" in unused
    assert "ExitPlanMode" not in unused          # used once in sess-1
    assert "EnterPlanMode" in unused             # separate row, genuinely never called
    assert "ToolSearch" not in unused            # only a subagent used it — still owner-side


def test_primitive_rows_split_owner_subagent_fleet(projects_dir, fake_home):
    report = _report(projects_dir, fake_home)
    rows = {row["feature"]: row for row in report["primitives"]}
    assert rows["ToolSearch"]["owner_calls"] == 0
    assert rows["ToolSearch"]["subagent_calls"] == 1
    assert rows["Agent"]["owner_calls"] == 2
    assert rows["Agent"]["fleet_calls"] == 1
    assert rows["Agent"]["total_calls"] == 3
    assert rows["ExitPlanMode"]["label"] == "plan mode (ExitPlanMode)"


def test_json_shape_and_render(projects_dir, fake_home):
    report = _report(projects_dir, fake_home, servers=[])

    for key in (
        "window_days", "since", "generated_at", "stats", "notes", "sessions",
        "projects_by_sessions", "primitives", "primitives_never_used_by_owner", "skills",
        "cli_commands", "agents", "mcp", "models", "hooks", "coverage",
    ):
        assert key in report
    assert json.loads(json.dumps(report))  # must be JSON-serializable end to end

    # Non-zero counts, so an all-empty report can never pass this test.
    assert report["sessions"]["owner"] == 2
    assert report["sessions"]["fleet_workers"] == 1
    assert sum(row["total_calls"] for row in report["primitives"]) > 0
    assert report["coverage"]["skills_used_by_owner"] == 2

    text = fu.render_report(report, scan_seconds=1.25)
    assert "PLATFORM PRIMITIVES" in text
    assert "plan mode (ExitPlanMode)" in text
    assert "CLI commands" in text
    assert "Available but never used" in text
    assert "Hook executions do not appear in transcripts" in text
    assert "capability-catalogue" in text
    assert "Coverage: the owner used" in text

    # The used-but-not-installed line must appear when such a skill was observed.
    report["skills"]["used_not_installed"] = ["some-other-repo-skill"]
    assert "Observed but NOT in the installed inventory" in fu.render_report(report)


def test_collect_emits_slug_buckets(projects_dir, fake_home):
    report = fu.collect(projects_dir, days=30, repos=[], home=fake_home, now=NOW)
    assert report["slug_buckets"] == {
        "D--Abhay-GetWorkDone-workspaces-cbp-T999": "fleet-workers",
        "D--Abhay-Ventures-demo": "owner",
    }


def test_hook_events_and_mcp_config_report_missing_files_honestly(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"hooks": {"UserPromptSubmit": [], "Stop": []}}), encoding="utf-8")
    events = fu.hook_events([settings, tmp_path / "missing.json"])
    assert events[str(settings)]["events"] == ["Stop", "UserPromptSubmit"]
    assert "unverified" in events[str(tmp_path / "missing.json")]["note"]

    config = fu.configured_mcp_servers(tmp_path / "absent.json", repos=[tmp_path])
    assert config["servers"] == []
    assert len(config["notes"]) == 2  # missing ~/.claude.json + missing repo .mcp.json
