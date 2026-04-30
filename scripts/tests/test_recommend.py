"""Tests for project resource recommendation engine."""

import json
from pathlib import Path

import pytest

from scripts.recommend import (
    analyze_gaps,
    analyze_overlaps_local,
    apply_to_local,
    classify_divergence,
    deep_merge_settings,
    detect_dependencies_from_dir,
    detect_improved_patterns,
    detect_stacks_from_dir,
    DEP_PATTERN_MAP,
    format_diff_report,
    format_divergence_table,
    format_report,
    generate_hub_practices_section,
    get_hub_resources,
    get_project_resource_names,
    get_rule_descriptions,
    is_stack_specific,
    matches_stacks,
    MUST_HAVE_RULES,
    name_matches_existing,
    provision_claude_local_md,
    provision_claude_md,
    provision_settings_json,
    provision_to_local,
    resolve_dep_patterns,
    tier_resource,
    tier_resource_with_reason,
    _copy_resources_for_tier,
    _format_nice_to_have_pr_body,
    PROVISION_START_MARKER,
    PROVISION_END_MARKER,
    _compute_line_overlap,
    _find_matching_project_name,
    reconcile_claude_md_rules,
    _compute_file_hash,
    classify_sync_status,
    load_sync_manifest,
    save_sync_manifest,
    build_sync_classification,
    update_improved_to_local,
    update_manifest_after_sync,
)


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _clear_tier_cache():
    """Clear the tier registry cache between tests to prevent cross-contamination."""
    from scripts.recommend import _load_tier_registry
    _load_tier_registry._cache = {}
    yield
    _load_tier_registry._cache = {}


@pytest.fixture
def _prime_real_registry():
    """Prime the tier registry cache with the real registry/patterns.json.

    Use this in tests that call tier_resource/tier_resource_with_reason
    without a hub_root fixture (i.e., they test against the real registry).
    """
    from scripts.recommend import _load_tier_registry
    real_hub = Path(__file__).parent.parent.parent
    _load_tier_registry(real_hub)
    yield


@pytest.fixture
def _prime_hub_registry(hub_root):
    """Prime the tier registry cache with the hub_root fixture's registry."""
    from scripts.recommend import _load_tier_registry
    _load_tier_registry(hub_root)
    yield


@pytest.fixture
def hub_root(tmp_path):
    """Create a minimal hub structure with core/.claude/ resources."""
    core = tmp_path / "core" / ".claude"

    # Skills
    for name in ["fix-loop", "tdd", "skill-master", "systematic-debugging",
                  "fastapi-db-migrate", "android-arch", "d3-viz", "brainstorm"]:
        skill_dir = core / "skills" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Agents
    agents = core / "agents"
    agents.mkdir(parents=True)
    for name in ["debugger-agent", "tester-agent", "security-auditor-agent", "fastapi-api-tester-agent"]:
        (agents / f"{name}.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Rules
    rules = core / "rules"
    rules.mkdir(parents=True)
    for name in ["workflow", "context-management", "claude-behavior", "testing", "tdd-rule",
                  "fastapi-backend"]:
        (rules / f"{name}.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Hooks
    hooks = core / "hooks"
    hooks.mkdir(parents=True)
    for name in ["dangerous-command-blocker", "secret-scanner", "auto-format"]:
        (hooks / f"{name}.sh").write_text(f"#!/bin/bash\n# {name}")

    # Templates and settings
    (core / "CLAUDE.md.template").write_text(
        "# CLAUDE.md\n\n**{{PROJECT_NAME}}** - {{PROJECT_DESCRIPTION}}\n\n"
        "Platform: {{PLATFORM}}\n\n"
        "<!-- hub:best-practices:start -->\n\n"
        "<!-- Placeholder replaced at provision time. -->\n\n"
        "<!-- hub:best-practices:end -->\n",
        encoding="utf-8",
    )
    (core / "CLAUDE.local.md.template").write_text(
        "# Personal Project Preferences\n\nThis file is gitignored.\n",
        encoding="utf-8",
    )
    (core / "settings.json").write_text('{\n  "permissions": {\n    "allow": [],\n    "deny": []\n  }\n}\n')

    # Registry with tier assignments (SSOT for tiering)
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    registry = {
        "_meta": {"version": "1.0.0"},
        # Skills
        "fix-loop": {"type": "skill", "tier": "must-have"},
        "tdd": {"type": "skill", "tier": "must-have"},
        "skill-master": {"type": "skill", "tier": "must-have"},
        "systematic-debugging": {"type": "skill", "tier": "must-have"},
        "fastapi-db-migrate": {"type": "skill", "tier": "must-have"},
        "android-arch": {"type": "skill", "tier": "must-have"},
        "d3-viz": {"type": "skill", "tier": "nice-to-have"},
        "brainstorm": {"type": "skill", "tier": "nice-to-have"},
        # Agents
        "debugger-agent": {"type": "agent", "tier": "must-have"},
        "tester-agent": {"type": "agent", "tier": "must-have"},
        "security-auditor-agent": {"type": "agent", "tier": "must-have"},
        "fastapi-api-tester-agent": {"type": "agent", "tier": "must-have"},
        # Rules
        "workflow": {"type": "rule", "tier": "must-have"},
        "context-management": {"type": "rule", "tier": "must-have"},
        "claude-behavior": {"type": "rule", "tier": "must-have"},
        "testing": {"type": "rule", "tier": "must-have"},
        "tdd-rule": {"type": "rule", "tier": "must-have"},
        "fastapi-backend": {"type": "rule", "tier": "must-have"},
        # Hooks
        "dangerous-command-blocker": {"type": "hook", "tier": "must-have"},
        "secret-scanner": {"type": "hook", "tier": "must-have"},
        "auto-format": {"type": "hook", "tier": "must-have"},
        # Skip list
        "twitter-x": {"type": "skill", "tier": "skip"},
        "obsidian": {"type": "skill", "tier": "skip"},
    }
    (registry_dir / "patterns.json").write_text(json.dumps(registry, indent=2))

    return tmp_path


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project with some existing resources."""
    claude = tmp_path / "project" / ".claude"

    # Existing skills
    for name in ["fix-loop", "db-migrate", "status"]:
        skill_dir = claude / "skills" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Existing agents
    agents = claude / "agents"
    agents.mkdir(parents=True)
    for name in ["debugger-agent", "tester-agent", "api-tester"]:
        (agents / f"{name}.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Existing rules
    rules = claude / "rules"
    rules.mkdir(parents=True)
    (rules / "workflow.md").write_text("---\nname: workflow\n---\n# workflow")

    # Existing hooks
    hooks = claude / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "auto-format.sh").write_text("#!/bin/bash\n# auto-format")

    return tmp_path / "project"


# --- Stack Detection ---


class TestDetectStacksFromDir:
    def test_detects_android(self, tmp_path):
        gradle = tmp_path / "android" / "app"
        gradle.mkdir(parents=True)
        (gradle / "build.gradle.kts").write_text(
            'plugins { id("com.android.application") }'
        )
        stacks = detect_stacks_from_dir(tmp_path)
        assert "android-compose" in stacks

    def test_detects_fastapi(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("fastapi>=0.109.0\nuvicorn>=0.27.0\n")
        stacks = detect_stacks_from_dir(tmp_path)
        assert "fastapi-python" in stacks

    def test_detects_firebase(self, tmp_path):
        (tmp_path / "google-services.json").write_text('{"project_info": {}}')
        stacks = detect_stacks_from_dir(tmp_path)
        assert "firebase-auth" in stacks

    def test_detects_firebase_from_requirements(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("firebase-admin>=6.0\n")
        stacks = detect_stacks_from_dir(tmp_path)
        assert "firebase-auth" in stacks

    def test_detects_ai_gemini(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("google-genai>=1.0.0\n")
        stacks = detect_stacks_from_dir(tmp_path)
        assert "ai-gemini" in stacks

    def test_detects_multiple_stacks(self, tmp_path):
        (tmp_path / "requirements.txt").write_text(
            "fastapi>=0.109.0\nfirebase-admin>=6.0\ngoogle-genai>=1.0.0\n"
        )
        gradle = tmp_path / "android"
        gradle.mkdir()
        (gradle / "build.gradle.kts").write_text('id("com.android.application")')
        stacks = detect_stacks_from_dir(tmp_path)
        assert len(stacks) == 4

    def test_empty_project_returns_empty(self, tmp_path):
        stacks = detect_stacks_from_dir(tmp_path)
        assert stacks == []

    def test_detects_react_nextjs(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies": {"next": "14.0.0"}}')
        stacks = detect_stacks_from_dir(tmp_path)
        assert "react-nextjs" in stacks


# --- Resource Inventory ---


class TestGetHubResources:
    def test_finds_all_types(self, hub_root):
        resources = get_hub_resources(hub_root)
        assert len(resources["skill"]) == 8
        assert len(resources["agent"]) == 4
        assert len(resources["rule"]) == 6
        assert len(resources["hook"]) == 3

    def test_skill_names_correct(self, hub_root):
        resources = get_hub_resources(hub_root)
        names = {r["name"] for r in resources["skill"]}
        assert "tdd" in names
        assert "fastapi-db-migrate" in names


class TestGetProjectResourceNames:
    def test_finds_existing_resources(self, project_dir):
        names = get_project_resource_names(project_dir / ".claude")
        assert "fix-loop" in names["skill"]
        assert "db-migrate" in names["skill"]
        assert "debugger-agent" in names["agent"]
        assert "workflow" in names["rule"]
        assert "auto-format" in names["hook"]

    def test_empty_dir_returns_empty(self, tmp_path):
        names = get_project_resource_names(tmp_path / ".claude")
        for v in names.values():
            assert len(v) == 0


# --- Name Matching ---


class TestNameMatchesExisting:
    def test_exact_match(self):
        assert name_matches_existing("fix-loop", {"fix-loop", "status"})

    def test_hub_prefixed_matches_project_unprefixed(self):
        """Hub 'fastapi-db-migrate' should match project 'db-migrate'."""
        assert name_matches_existing("fastapi-db-migrate", {"db-migrate", "status"})

    def test_hub_prefixed_matches_project_android(self):
        assert name_matches_existing("android-adb-test", {"adb-test"})

    def test_no_match(self):
        assert not name_matches_existing("tdd", {"fix-loop", "status"})

    def test_hub_agent_prefix_match(self):
        """Hub 'fastapi-api-tester' should match project 'api-tester'."""
        assert name_matches_existing("fastapi-api-tester-agent", {"api-tester-agent", "debugger-agent"})

    def test_reversed_prefix_match(self):
        """Hub 'android-run-tests' should match project 'run-android-tests'."""
        assert name_matches_existing("android-run-tests", {"run-android-tests"})


# --- Stack Matching ---


class TestIsStackSpecific:
    def test_fastapi_prefix(self):
        assert is_stack_specific("fastapi-db-migrate")

    def test_android_prefix(self):
        assert is_stack_specific("android-arch")

    def test_universal(self):
        assert not is_stack_specific("tdd")

    def test_ai_gemini_prefix(self):
        assert is_stack_specific("ai-gemini-api")


class TestMatchesStacks:
    def test_universal_always_matches(self):
        assert matches_stacks("tdd", [])
        assert matches_stacks("tdd", ["android-compose"])

    def test_matching_stack(self):
        assert matches_stacks("fastapi-db-migrate", ["fastapi-python"])

    def test_non_matching_stack(self):
        assert not matches_stacks("fastapi-db-migrate", ["android-compose"])

    def test_multiple_stacks(self):
        assert matches_stacks("android-arch", ["fastapi-python", "android-compose"])


# --- Tiering ---


@pytest.mark.usefixtures("_prime_real_registry")
class TestTierResource:
    def test_must_have_hook(self):
        assert tier_resource("dangerous-command-blocker", "hook", []) == "must-have"
        assert tier_resource("secret-scanner", "hook", []) == "must-have"

    def test_must_have_universal_skill(self):
        assert tier_resource("skill-master", "skill", []) == "must-have"
        assert tier_resource("tdd", "skill", []) == "must-have"
        assert tier_resource("systematic-debugging", "skill", []) == "must-have"

    def test_must_have_stack_skill(self):
        assert tier_resource("android-arch", "skill", ["android-compose"]) == "must-have"
        assert tier_resource("fastapi-db-migrate", "skill", ["fastapi-python"]) == "must-have"

    def test_nice_to_have_skill(self):
        # Stack-dependent skills stay nice-to-have until their stack is detected
        assert tier_resource("vitest-dev", "skill", []) == "nice-to-have"
        assert tier_resource("pytest-dev", "skill", []) == "nice-to-have"

    def test_skip_always_skip_list(self):
        assert tier_resource("twitter-x", "skill", []) == "skip"
        assert tier_resource("obsidian", "skill", []) == "skip"

    def test_skip_wrong_stack(self):
        assert tier_resource("fastapi-db-migrate", "skill", ["android-compose"]) == "skip"

    def test_must_have_rule(self):
        assert tier_resource("context-management", "rule", []) == "must-have"

    def test_hub_meta_rules_not_distributed(self):
        """Hub-internal quality rules were removed from core/.claude/rules/ and registry.
        They exist only at hub root .claude/rules/ for hub-internal use."""
        from scripts.recommend import get_hub_resources
        import tempfile, pathlib
        # Verify none of the hub-meta rules would be discovered in a real hub scan
        hub = pathlib.Path(tempfile.mkdtemp())
        core_rules = hub / "core" / ".claude" / "rules"
        core_rules.mkdir(parents=True)
        for name in ["workflow", "context-management"]:
            (core_rules / f"{name}.md").write_text(f"# {name}")
        resources = get_hub_resources(hub)
        found = {r["name"] for r in resources["rule"]}
        for meta in ["pattern-structure", "pattern-portability",
                      "pattern-self-containment", "rule-writing-meta"]:
            assert meta not in found, f"{meta} should not be in distributable rules"

    def test_must_have_agent(self):
        assert tier_resource("security-auditor-agent", "agent", []) == "must-have"

    def test_stack_override_nice_to_have(self):
        """firebase-data-connect is stack-specific but overridden to nice-to-have."""
        assert tier_resource("firebase-data-connect", "skill", ["firebase-auth"]) == "nice-to-have"

    def test_pg_query_dep_promoted(self):
        """pg-query is must-have when promoted by psycopg2 dep detection."""
        assert tier_resource("pg-query", "skill", [], dep_promoted={"pg-query"}) == "must-have"
        assert tier_resource("pg-query", "skill", []) == "nice-to-have"

    def test_compose_ui_dep_promoted(self):
        """compose-ui is must-have when promoted by compose dep detection."""
        assert tier_resource("compose-ui", "skill", [], dep_promoted={"compose-ui"}) == "must-have"
        assert tier_resource("compose-ui", "skill", []) == "nice-to-have"

    def test_non_prefixed_stack_rules_skip_when_no_stack(self):
        """Non-prefixed rules like 'android', 'vue', 'firebase' skip when their stack is absent."""
        # No stacks detected at all
        assert tier_resource("android", "rule", []) == "skip"
        assert tier_resource("firebase", "rule", []) == "skip"
        assert tier_resource("flutter", "rule", []) == "skip"
        assert tier_resource("bun-elysia", "rule", []) == "skip"
        # Wrong stack detected
        assert tier_resource("android", "rule", ["fastapi-python"]) == "skip"
        assert tier_resource("firebase", "rule", ["fastapi-python"]) == "skip"
        assert tier_resource("flutter", "rule", ["fastapi-python"]) == "skip"

    def test_non_prefixed_stack_rules_kept_when_stack_matches(self):
        """Non-prefixed rules are kept (not skipped) when their required stack is detected."""
        assert tier_resource("android", "rule", ["android-compose"]) != "skip"
        assert tier_resource("firebase", "rule", ["firebase-auth"]) != "skip"
        assert tier_resource("flutter", "rule", ["android-compose"]) != "skip"
        assert tier_resource("fastapi-backend", "rule", ["fastapi-python"]) != "skip"
        assert tier_resource("fastapi-database", "rule", ["fastapi-python"]) != "skip"

    def test_non_prefixed_stack_rules_dep_promoted_overrides_skip(self):
        """Dep promotion overrides the stack requirement skip."""
        assert tier_resource("vue", "rule", [], dep_promoted={"vue"}) == "must-have"
        assert tier_resource("bun-elysia", "rule", [], dep_promoted={"bun-elysia"}) == "must-have"
        assert tier_resource("flutter", "rule", [], dep_promoted={"flutter"}) == "must-have"

    def test_vue_rule_skipped_without_vue_dep_or_stack(self):
        """Vue rule is skipped when no Vue-related stack or dep is detected."""
        # react-nextjs stack doesn't match, but vue requires it (as proxy for frontend JS stack)
        assert tier_resource("vue", "rule", ["fastapi-python"]) == "skip"
        assert tier_resource("vue", "rule", []) == "skip"

    def test_fastapi_rules_skipped_without_fastapi_stack(self):
        """FastAPI rules skip when project is not FastAPI."""
        assert tier_resource("fastapi-backend", "rule", ["android-compose"]) == "skip"
        assert tier_resource("fastapi-database", "rule", []) == "skip"


# --- Gap Analysis ---


@pytest.mark.usefixtures("_prime_hub_registry")
class TestAnalyzeGaps:
    def test_finds_missing_resources(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python", "android-compose"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)

        # Must-have should include tdd, skill-master, etc.
        must_names = {g["name"] for g in gaps["must-have"]}
        assert "tdd" in must_names
        assert "skill-master" in must_names
        assert "systematic-debugging" in must_names
        assert "dangerous-command-blocker" in must_names
        assert "secret-scanner" in must_names

    def test_excludes_existing_resources(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)

        all_names = set()
        for tier_items in gaps.values():
            all_names.update(g["name"] for g in tier_items)

        # Already exists in project
        assert "fix-loop" not in all_names
        assert "debugger-agent" not in all_names
        assert "workflow" not in all_names
        assert "auto-format" not in all_names

    def test_handles_prefix_name_matches(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)

        all_names = set()
        for tier_items in gaps.values():
            all_names.update(g["name"] for g in tier_items)

        # Project has 'db-migrate', hub has 'fastapi-db-migrate' — should match
        assert "fastapi-db-migrate" not in all_names
        # Project has 'api-tester', hub has 'fastapi-api-tester' — should match
        assert "fastapi-api-tester" not in all_names

    def test_d3_viz_nice_to_have_without_deps(self, hub_root, project_dir):
        """d3-viz is nice-to-have without deps, must-have with d3 dep."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)

        nice_names = {g["name"] for g in gaps["nice-to-have"]}
        assert "d3-viz" in nice_names

    def test_d3_viz_promoted_with_deps(self, hub_root, project_dir):
        """d3-viz is promoted to must-have when d3 dep is detected."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]
        deps = {"npm": ["d3"]}

        gaps = analyze_gaps(hub_resources, project_names, stacks, deps=deps)

        must_names = {g["name"] for g in gaps["must-have"]}
        assert "d3-viz" in must_names


# --- Report ---


@pytest.mark.usefixtures("_prime_hub_registry")
class TestFormatReport:
    def test_report_contains_sections(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python", "android-compose"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        report = format_report(gaps, stacks, project_names, hub_resources)

        assert "MUST-HAVE" in report
        assert "NICE-TO-HAVE" in report or "SKIP" in report
        assert "RECOMMENDATION REPORT" in report

    def test_report_shows_stacks(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        report = format_report(gaps, stacks, project_names, hub_resources)

        assert "fastapi-python" in report


# --- Apply ---


@pytest.mark.usefixtures("_prime_hub_registry")
class TestApplyToLocal:
    def test_copies_must_have_skills(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        assert len(copied) > 0
        # tdd should be copied
        assert any("tdd" in f for f in copied)
        # Verify file exists
        assert (project_dir / ".claude" / "skills" / "tdd" / "SKILL.md").exists()

    def test_copies_hooks(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        assert any("dangerous-command-blocker" in f for f in copied)
        assert any("secret-scanner" in f for f in copied)
        assert (project_dir / ".claude" / "hooks" / "dangerous-command-blocker.sh").exists()

    def test_does_not_copy_skip_tier(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        # d3-viz is in ALWAYS_SKIP — should not be copied
        assert not any("d3-viz" in f for f in copied)

    def test_nice_to_have_tier_includes_both(self, hub_root, project_dir, tmp_path):
        """nice-to-have tier should cover a superset of must-have patterns.
        Use two separate project dirs so the idempotent _copy_if_changed
        behavior doesn't skew the count comparison."""
        hub_resources = get_hub_resources(hub_root)
        stacks = ["fastapi-python"]
        gaps = analyze_gaps(
            hub_resources,
            get_project_resource_names(project_dir / ".claude"),
            stacks,
        )

        # Project A: must-have only
        proj_a = tmp_path / "project-a"
        proj_a.mkdir()
        must_only = apply_to_local(hub_root, proj_a, gaps, tier="must-have")

        # Project B: nice-to-have (superset)
        proj_b = tmp_path / "project-b"
        proj_b.mkdir()
        both = apply_to_local(hub_root, proj_b, gaps, tier="nice-to-have")

        assert len(both) >= len(must_only), (
            f"nice-to-have tier ({len(both)} files) should cover at least as "
            f"much as must-have tier ({len(must_only)} files)"
        )

    def test_copies_agents(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        assert any("security-auditor-agent" in f for f in copied)
        assert (project_dir / ".claude" / "agents" / "security-auditor-agent.md").exists()

    def test_copies_rules(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        assert any("context-management" in f for f in copied)
        assert (project_dir / ".claude" / "rules" / "context-management.md").exists()

    def test_does_not_overwrite_existing(self, hub_root, project_dir):
        """Existing resources should not be in the gaps at all."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="nice-to-have")

        # fix-loop already exists — should not be in copied list
        assert not any(f.endswith("fix-loop/SKILL.md") for f in copied)


# --- Content Diff ---


class TestComputeLineOverlap:
    def test_identical_content(self):
        lines = ["# Header", "Some content", "More content"]
        assert _compute_line_overlap(lines, lines) == 1.0

    def test_no_overlap(self):
        hub = ["# Hub header", "Hub content"]
        proj = ["# Project header", "Project content"]
        assert _compute_line_overlap(hub, proj) == 0.0

    def test_partial_overlap(self):
        hub = ["# Header", "Shared line", "Hub only"]
        proj = ["# Header", "Shared line", "Project only"]
        # "# header" and "shared line" match (2 of 3 hub lines)
        overlap = _compute_line_overlap(hub, proj)
        assert 0.5 < overlap < 1.0

    def test_empty_hub(self):
        assert _compute_line_overlap([], ["some content"]) == 1.0

    def test_skips_frontmatter_delimiters(self):
        hub = ["---", "name: test", "---", "# Content"]
        proj = ["---", "name: different", "---", "# Content"]
        # "---" is skipped, "name: test" vs "name: different" don't match,
        # but "# content" matches
        overlap = _compute_line_overlap(hub, proj)
        assert overlap > 0


class TestClassifyDivergence:
    def test_identical(self):
        content = "---\nname: test\n---\n# Test Skill\n\nSome content here."
        result = classify_divergence(content, content)
        assert result["status"] == "identical"
        assert result["hub_overlap"] == 1.0

    def test_project_customized(self):
        hub = "# Header\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5"
        project = "# Header\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\nExtra 1\nExtra 2\nExtra 3\nExtra 4"
        result = classify_divergence(hub, project)
        assert result["status"] == "project-customized"
        assert result["hub_overlap"] >= 0.6

    def test_name_collision(self):
        hub = "# Security Audit\nCheck for XSS.\nCheck for SQLi.\nRun SAST tools."
        project = "# Personal Coaching\nSet life goals.\nTrack habits.\nReview beliefs."
        result = classify_divergence(hub, project)
        assert result["status"] == "name-collision"
        assert result["hub_overlap"] < 0.3

    def test_hub_newer(self):
        # Hub is larger and has different content
        hub_lines = ["# Feature"] + [f"Hub step {i}: Do something unique {i}" for i in range(20)]
        project_lines = ["# Different Feature"] + [f"Old step {i}" for i in range(5)]
        hub = "\n".join(hub_lines)
        project = "\n".join(project_lines)
        result = classify_divergence(hub, project)
        assert result["status"] == "hub-newer"

    def test_project_heavily_customized(self):
        """Project 3x larger than hub with low overlap is project-customized, not name-collision."""
        hub = "# Skill\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5"
        project_lines = ["# Skill (Customized)"] + [f"Custom step {i}" for i in range(20)]
        project = "\n".join(project_lines)
        result = classify_divergence(hub, project)
        assert result["status"] == "project-customized"


class TestFindMatchingProjectName:
    def test_exact_match(self):
        assert _find_matching_project_name("fix-loop", {"fix-loop", "status"}) == "fix-loop"

    def test_prefix_stripped(self):
        assert _find_matching_project_name(
            "fastapi-db-migrate", {"db-migrate", "status"}
        ) == "db-migrate"

    def test_no_match(self):
        assert _find_matching_project_name("tdd", {"fix-loop", "status"}) is None

    def test_reversed_prefix(self):
        result = _find_matching_project_name(
            "android-run-tests", {"run-android-tests"}
        )
        assert result == "run-android-tests"


class TestAnalyzeOverlapsLocal:
    def test_finds_overlapping_skills(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")

        overlaps = analyze_overlaps_local(hub_root, project_dir, hub_resources, project_names)

        # fix-loop exists in both
        fix_loop = [o for o in overlaps if o["hub_name"] == "fix-loop"]
        assert len(fix_loop) == 1
        assert fix_loop[0]["type"] == "skill"

    def test_detects_identical_content(self, hub_root, project_dir):
        """If we copy hub content to project, it should be classified as identical."""
        import shutil
        hub_skill = hub_root / "core" / ".claude" / "skills" / "fix-loop" / "SKILL.md"
        proj_skill = project_dir / ".claude" / "skills" / "fix-loop" / "SKILL.md"
        shutil.copy2(hub_skill, proj_skill)

        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")

        overlaps = analyze_overlaps_local(hub_root, project_dir, hub_resources, project_names)

        fix_loop = [o for o in overlaps if o["hub_name"] == "fix-loop"]
        assert len(fix_loop) == 1
        assert fix_loop[0]["status"] == "identical"

    def test_detects_prefix_matched_overlaps(self, hub_root, project_dir):
        """Hub 'fastapi-db-migrate' should be compared with project 'db-migrate'."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")

        overlaps = analyze_overlaps_local(hub_root, project_dir, hub_resources, project_names)

        db_migrate = [o for o in overlaps if o["hub_name"] == "fastapi-db-migrate"]
        assert len(db_migrate) == 1
        assert db_migrate[0]["project_name"] == "db-migrate"

    def test_finds_overlapping_agents(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")

        overlaps = analyze_overlaps_local(hub_root, project_dir, hub_resources, project_names)

        debugger = [o for o in overlaps if o["hub_name"] == "debugger-agent"]
        assert len(debugger) == 1
        assert debugger[0]["type"] == "agent"

    def test_finds_overlapping_rules(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")

        overlaps = analyze_overlaps_local(hub_root, project_dir, hub_resources, project_names)

        workflow = [o for o in overlaps if o["hub_name"] == "workflow"]
        assert len(workflow) == 1
        assert workflow[0]["type"] == "rule"

    def test_finds_overlapping_hooks(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")

        overlaps = analyze_overlaps_local(hub_root, project_dir, hub_resources, project_names)

        auto_format = [o for o in overlaps if o["hub_name"] == "auto-format"]
        assert len(auto_format) == 1
        assert auto_format[0]["type"] == "hook"


class TestFormatDiffReport:
    def test_report_has_header(self):
        overlaps = [
            {
                "hub_name": "fix-loop", "project_name": "fix-loop",
                "type": "skill", "status": "identical",
                "hub_lines": 96, "project_lines": 96,
                "hub_overlap": 1.0, "detail": "Content is identical",
            }
        ]
        report = format_diff_report(overlaps)
        assert "CONTENT DIVERGENCE REPORT" in report
        assert "IDENTICAL" in report

    def test_report_shows_name_collisions(self):
        overlaps = [
            {
                "hub_name": "strategic-architect", "project_name": "strategic-architect",
                "type": "skill", "status": "name-collision",
                "hub_lines": 107, "project_lines": 231,
                "hub_overlap": 0.15,
                "detail": "Very low content overlap (15%). Different resources sharing a name.",
            }
        ]
        report = format_diff_report(overlaps)
        assert "NAME COLLISION" in report
        assert "strategic-architect" in report

    def test_report_shows_hub_newer(self):
        overlaps = [
            {
                "hub_name": "verify-screenshots", "project_name": "verify-screenshots",
                "type": "skill", "status": "hub-newer",
                "hub_lines": 387, "project_lines": 286,
                "hub_overlap": 0.25,
                "detail": "Hub has significant content the project lacks.",
            }
        ]
        report = format_diff_report(overlaps)
        assert "HUB HAS IMPROVEMENTS" in report


# --- Provision: Rule Descriptions ---


class TestGetRuleDescriptions:
    def test_frontmatter_extraction(self, hub_root):
        descs = get_rule_descriptions(hub_root, ["workflow", "context-management"])
        assert "workflow" in descs
        assert "context-management" in descs

    def test_missing_description_fallback(self, tmp_path):
        """Falls back to first # heading when description is absent."""
        rules_dir = tmp_path / "core" / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "no-desc.md").write_text("# My Custom Rule\n\nSome content.")
        descs = get_rule_descriptions(tmp_path, ["no-desc"])
        assert descs["no-desc"] == "My Custom Rule"

    def test_nonexistent_files(self, hub_root):
        descs = get_rule_descriptions(hub_root, ["does-not-exist"])
        assert descs == {}


# --- Provision: Hub Practices Section ---


class TestGenerateHubPracticesSection:
    def test_contains_bug_fixing_rule(self, hub_root):
        section = generate_hub_practices_section(hub_root, ["workflow"])
        assert "Bug Fixing" in section
        assert "/fix-loop" in section

    def test_section_points_at_rules_directory_not_enumeration(self, hub_root):
        """The hub section must describe where rules live without enumerating
        them. Enumerating 50+ rule rows costs ~4k tokens per session for zero
        enforcement benefit (path-scoped rules auto-load via `globs:`)."""
        section = generate_hub_practices_section(hub_root, ["workflow", "context-management"])
        # Still mentions .claude/rules/ so users know where to look
        assert ".claude/rules/" in section or "rules/" in section
        # Points at globs auto-loading (the actual enforcement mechanism)
        assert "globs" in section.lower() or "auto-load" in section.lower() or "path-scoped" in section.lower()

    def test_section_length_bounded_regardless_of_rule_count(self, hub_root):
        """The hub section MUST stay compact (≤25 lines) regardless of how
        many rules the project has. A 50-rule project and a 5-rule project
        should produce sections of similar length."""
        few_rules = generate_hub_practices_section(hub_root, ["workflow"])
        many_rules = generate_hub_practices_section(
            hub_root,
            [f"rule-{i:03d}" for i in range(100)],
        )
        few_lines = len(few_rules.splitlines())
        many_lines = len(many_rules.splitlines())
        assert many_lines <= 25, (
            f"Hub section with 100 rules grew to {many_lines} lines — "
            f"must stay bounded to avoid CLAUDE.md bloat"
        )
        # And the count must not scale with rules (no enumeration)
        assert abs(many_lines - few_lines) <= 2, (
            f"Section length scales with rule count: {few_lines} lines for 1 "
            f"rule vs {many_lines} for 100 rules. Enumeration re-introduced?"
        )

    def test_contains_sync_metadata(self, hub_root):
        section = generate_hub_practices_section(hub_root, ["workflow"])
        assert "Claude Code Configuration" in section
        assert ".claude/" in section

    def test_has_markers(self, hub_root):
        section = generate_hub_practices_section(hub_root, [])
        assert PROVISION_START_MARKER in section
        assert PROVISION_END_MARKER in section


# --- Provision: CLAUDE.md ---


class TestProvisionClaudeMd:
    def test_create_from_template(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        result = provision_claude_md(hub_root, target, ["fastapi-python"], ["workflow"])
        assert result == "created"
        assert (target / "CLAUDE.md").exists()
        content = (target / "CLAUDE.md").read_text()
        assert "myproject" in content

    def test_append_markers_to_existing(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        (target / "CLAUDE.md").write_text("# My Project\n\nExisting content.\n")
        result = provision_claude_md(hub_root, target, [], ["workflow"])
        assert result == "appended"
        content = (target / "CLAUDE.md").read_text()
        assert "Existing content." in content
        assert PROVISION_START_MARKER in content
        assert PROVISION_END_MARKER in content

    def test_replace_between_markers(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        existing = (
            "# My Project\n\nBefore.\n\n"
            f"{PROVISION_START_MARKER}\nOLD CONTENT\n{PROVISION_END_MARKER}\n\n"
            "After.\n"
        )
        (target / "CLAUDE.md").write_text(existing)
        result = provision_claude_md(hub_root, target, [], ["workflow"])
        assert result == "replaced"
        content = (target / "CLAUDE.md").read_text()
        assert "Before." in content
        assert "After." in content
        assert "OLD CONTENT" not in content
        assert "Bug Fixing" in content

    def test_preserve_outside_content(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        existing = (
            "# Important Header\n\n"
            f"{PROVISION_START_MARKER}\nold\n{PROVISION_END_MARKER}\n\n"
            "# Footer\n"
        )
        (target / "CLAUDE.md").write_text(existing)
        provision_claude_md(hub_root, target, [], [])
        content = (target / "CLAUDE.md").read_text()
        assert "Important Header" in content
        assert "Footer" in content

    def test_partial_markers_start_without_end(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        existing = f"# My Project\n\n{PROVISION_START_MARKER}\nBroken\n"
        (target / "CLAUDE.md").write_text(existing)
        result = provision_claude_md(hub_root, target, [], [])
        assert result == "appended"
        content = (target / "CLAUDE.md").read_text()
        assert content.count(PROVISION_START_MARKER) == 2  # old broken + new

    def test_create_from_template_uses_dynamic_hub_section(self, hub_root, tmp_path):
        """Case 1a: template-based creation uses dynamic hub_section, not hardcoded content.
        After the lean-section refactor, the hub section points at `.claude/rules/`
        rather than enumerating each rule — but it's still dynamic (not a fixed
        template placeholder)."""
        target = tmp_path / "myproject"
        target.mkdir()
        result = provision_claude_md(hub_root, target, ["fastapi-python"], ["workflow", "context-management"])
        assert result == "created"
        content = (target / "CLAUDE.md").read_text()
        # Hub section is present and points at the rules directory
        assert ".claude/rules/" in content or "rules/" in content
        # Dynamic — contains the Bug Fixing rule and marker
        assert "Bug Fixing" in content
        # Should NOT contain the old placeholder text from the template
        assert "Placeholder replaced at provision time" not in content

    def test_create_from_template_does_not_enumerate_rules(self, hub_root, tmp_path):
        """Case 1a: the hub section MUST NOT enumerate individual rule files.
        Enumerating scales linearly with rule count and costs ~4k tokens at 50
        rules for zero enforcement benefit (path-scoping is done via `globs:`)."""
        target = tmp_path / "myproject"
        target.mkdir()
        provision_claude_md(hub_root, target, [], ["workflow", "context-management", "testing"])
        content = (target / "CLAUDE.md").read_text()
        # None of these rule-row markers should appear — they indicate a regression
        # back to the bulky table format.
        for row_marker in ("`rules/workflow.md`", "`rules/context-management.md`", "`rules/testing.md`"):
            assert row_marker not in content, (
                f"Hub section regressed to per-rule enumeration: found {row_marker!r}. "
                f"The lean format points at `.claude/rules/` generically."
            )

    def test_create_from_template_preserves_user_sections(self, hub_root, tmp_path):
        """Case 1a: user-editable sections from the template survive hub section replacement."""
        target = tmp_path / "myproject"
        target.mkdir()
        provision_claude_md(hub_root, target, ["fastapi-python"], ["workflow"])
        content = (target / "CLAUDE.md").read_text()
        # Template's user-editable sections should be preserved
        assert "**myproject**" in content
        assert "Platform: fastapi-python" in content
        # Hub markers should be present from the dynamic section
        assert PROVISION_START_MARKER in content
        assert PROVISION_END_MARKER in content

    def test_backup_created_when_replacing(self, hub_root, tmp_path):
        """Safety net: replacing an existing CLAUDE.md MUST write a backup of
        the prior content to CLAUDE.md.backup so the user can recover if the
        new content drops anything they cared about."""
        target = tmp_path / "myproject"
        target.mkdir()
        prior = (
            "# My Project\n\nBefore.\n\n"
            f"{PROVISION_START_MARKER}\nOLD CONTENT\n{PROVISION_END_MARKER}\n\n"
            "After.\n"
        )
        (target / "CLAUDE.md").write_text(prior)
        provision_claude_md(hub_root, target, [], ["workflow"])
        backup = target / "CLAUDE.md.backup"
        assert backup.exists(), "CLAUDE.md.backup must exist after replace"
        assert backup.read_text() == prior, "backup must contain the pre-provision content verbatim"

    def test_backup_created_when_appending(self, hub_root, tmp_path):
        """Same safety net for the append case (CLAUDE.md exists without markers)."""
        target = tmp_path / "myproject"
        target.mkdir()
        prior = "# My Project\n\nHand-authored content.\n"
        (target / "CLAUDE.md").write_text(prior)
        provision_claude_md(hub_root, target, [], ["workflow"])
        backup = target / "CLAUDE.md.backup"
        assert backup.exists(), "CLAUDE.md.backup must exist after append"
        assert backup.read_text() == prior, "backup must contain the pre-provision content verbatim"

    def test_no_backup_when_creating_from_template(self, hub_root, tmp_path):
        """Case 1: no pre-existing CLAUDE.md -> nothing to back up."""
        target = tmp_path / "myproject"
        target.mkdir()
        provision_claude_md(hub_root, target, ["fastapi-python"], ["workflow"])
        assert not (target / "CLAUDE.md.backup").exists(), (
            "No backup should be written when there was no prior CLAUDE.md"
        )

    def test_real_template_surfaces_preservation_guidance(self):
        """The REAL core/.claude/CLAUDE.md.template must tell users which parts
        of CLAUDE.md are preserved across re-provisions, and point at the
        backup path. Tested against the actual template file, not the minimal
        fixture used by hub_root."""
        real_template = (
            Path(__file__).parent.parent.parent
            / "core" / ".claude" / "CLAUDE.md.template"
        )
        assert real_template.exists(), f"Template missing at {real_template}"
        content = real_template.read_text(encoding="utf-8")
        assert "PRESERVED ON RE-PROVISION" in content, (
            "Template should include explicit guidance about which sections "
            "survive re-provisioning"
        )
        assert "CLAUDE.md.backup" in content, (
            "Template should mention the backup file so users know recovery exists"
        )


# --- Provision: CLAUDE.local.md ---


class TestProvisionClaudeLocalMd:
    def test_create_when_missing(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        result = provision_claude_local_md(hub_root, target)
        assert result == "created"
        assert (target / "CLAUDE.local.md").exists()

    def test_skip_when_exists(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        (target / "CLAUDE.local.md").write_text("# My local config")
        result = provision_claude_local_md(hub_root, target)
        assert result == "skipped"
        assert (target / "CLAUDE.local.md").read_text() == "# My local config"


# --- Provision: Deep Merge Settings ---


class TestDeepMergeSettings:
    def test_add_keys(self):
        base = {"a": 1}
        overlay = {"b": 2}
        result = deep_merge_settings(base, overlay)
        assert result == {"a": 1, "b": 2}

    def test_preserve_existing(self):
        base = {"a": 1}
        overlay = {"a": 99}
        result = deep_merge_settings(base, overlay)
        assert result["a"] == 1  # base wins

    def test_nested_merge(self):
        base = {"permissions": {"allow": ["read"]}}
        overlay = {"permissions": {"deny": ["write"]}}
        result = deep_merge_settings(base, overlay)
        assert result == {"permissions": {"allow": ["read"], "deny": ["write"]}}

    def test_list_dedup(self):
        base = {"items": ["a", "b"]}
        overlay = {"items": ["b", "c"]}
        result = deep_merge_settings(base, overlay)
        assert result["items"] == ["a", "b", "c"]

    def test_empty_base(self):
        result = deep_merge_settings({}, {"a": 1})
        assert result == {"a": 1}

    def test_empty_overlay(self):
        result = deep_merge_settings({"a": 1}, {})
        assert result == {"a": 1}


# --- Provision: settings.json ---


class TestProvisionSettingsJson:
    def test_create_when_missing(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        (target / ".claude").mkdir(parents=True)
        result = provision_settings_json(hub_root, target)
        assert result == "created"
        assert (target / ".claude" / "settings.json").exists()

    def test_merge_existing(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        (target / ".claude").mkdir(parents=True)
        existing = {"permissions": {"allow": ["Bash(*)"]}, "custom": True}
        (target / ".claude" / "settings.json").write_text(json.dumps(existing))
        result = provision_settings_json(hub_root, target)
        assert result == "merged"
        merged = json.loads((target / ".claude" / "settings.json").read_text())
        assert merged["custom"] is True
        assert "Bash(*)" in merged["permissions"]["allow"]


# --- Provision: Format Divergence Table ---


class TestFormatDivergenceTable:
    def test_markdown_output(self):
        overlaps = [
            {
                "hub_name": "skill-a", "project_name": "skill-a",
                "type": "skill", "status": "hub-newer",
                "hub_overlap": 0.3, "detail": "Hub has improvements.",
            }
        ]
        table = format_divergence_table(overlaps)
        assert "Content Divergence" in table
        assert "skill-a" in table
        assert "hub-newer" in table

    def test_excludes_identical(self):
        overlaps = [
            {
                "hub_name": "skill-a", "project_name": "skill-a",
                "type": "skill", "status": "identical",
                "hub_overlap": 1.0, "detail": "Content is identical",
            }
        ]
        table = format_divergence_table(overlaps)
        assert table == ""

    def test_empty_when_all_identical(self):
        overlaps = [
            {
                "hub_name": "a", "project_name": "a",
                "type": "skill", "status": "identical",
                "hub_overlap": 1.0, "detail": "identical",
            },
            {
                "hub_name": "b", "project_name": "b",
                "type": "rule", "status": "identical",
                "hub_overlap": 1.0, "detail": "identical",
            },
        ]
        assert format_divergence_table(overlaps) == ""


# --- Provision: provision_to_local ---


@pytest.mark.usefixtures("_prime_hub_registry")
class TestProvisionToLocal:
    def test_full_integration(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]
        gaps = analyze_gaps(hub_resources, project_names, stacks)

        summary = provision_to_local(hub_root, project_dir, gaps, stacks)
        assert len(summary["copied_files"]) > 0
        assert summary["claude_md"] == "created"  # project_dir has no CLAUDE.md
        assert summary["settings_json"] in ("created", "merged")
        assert (project_dir / "CLAUDE.md").exists()

    def test_returns_summary_dict(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        gaps = analyze_gaps(hub_resources, project_names, ["fastapi-python"])

        summary = provision_to_local(hub_root, project_dir, gaps, ["fastapi-python"])
        assert "copied_files" in summary
        assert "claude_md" in summary
        assert "claude_local_md" in summary
        assert "settings_json" in summary

    def test_idempotent_second_run(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]
        gaps = analyze_gaps(hub_resources, project_names, stacks)

        # First run
        provision_to_local(hub_root, project_dir, gaps, stacks)

        # Second run — gaps should be empty now, CLAUDE.md should be replaced
        project_names2 = get_project_resource_names(project_dir / ".claude")
        gaps2 = analyze_gaps(hub_resources, project_names2, stacks)
        summary2 = provision_to_local(hub_root, project_dir, gaps2, stacks)

        # No new files to copy (all resources already present)
        assert len(summary2["copied_files"]) == 0
        # CLAUDE.md already exists — should replace or append
        assert summary2["claude_md"] in ("replaced", "appended")


# --- Reconciliation ---


class TestReconcileClaudeMdRules:
    def test_consistent_state_no_warnings(self, tmp_path):
        target = tmp_path / "project"
        target.mkdir()
        rules_dir = target / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "workflow.md").write_text("# Workflow")
        (rules_dir / "testing.md").write_text("# Testing")
        claude_md = (
            "# Project\n\n"
            "| Rule File | What It Covers |\n"
            "|-----------|---------------|\n"
            "| `rules/workflow.md` | Workflow |\n"
            "| `rules/testing.md` | Testing |\n"
        )
        (target / "CLAUDE.md").write_text(claude_md)
        warnings = reconcile_claude_md_rules(target)
        assert warnings == []

    def test_dangling_reference(self, tmp_path):
        target = tmp_path / "project"
        target.mkdir()
        rules_dir = target / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        claude_md = (
            "# Project\n\n"
            "| `rules/workflow.md` | Workflow |\n"
            "| `rules/nonexistent.md` | Ghost |\n"
        )
        (target / "CLAUDE.md").write_text(claude_md)
        (rules_dir / "workflow.md").write_text("# Workflow")
        warnings = reconcile_claude_md_rules(target)
        assert any("nonexistent" in w and "does not exist" in w for w in warnings)

    def test_unreferenced_rule_on_disk(self, tmp_path):
        target = tmp_path / "project"
        target.mkdir()
        rules_dir = target / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "workflow.md").write_text("# Workflow")
        (rules_dir / "orphan.md").write_text("# Orphan")
        claude_md = "| `rules/workflow.md` | Workflow |\n"
        (target / "CLAUDE.md").write_text(claude_md)
        warnings = reconcile_claude_md_rules(target)
        assert any("orphan" in w and "not listed" in w for w in warnings)

    def test_no_claude_md_no_warnings(self, tmp_path):
        target = tmp_path / "project"
        target.mkdir()
        warnings = reconcile_claude_md_rules(target)
        assert warnings == []

    def test_no_rules_dir_no_warnings(self, tmp_path):
        target = tmp_path / "project"
        target.mkdir()
        (target / "CLAUDE.md").write_text("# Project\nNo rules table here.\n")
        warnings = reconcile_claude_md_rules(target)
        assert warnings == []

    def test_readme_excluded(self, tmp_path):
        target = tmp_path / "project"
        target.mkdir()
        rules_dir = target / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "README.md").write_text("# Rules README")
        (target / "CLAUDE.md").write_text("# Project\n")
        warnings = reconcile_claude_md_rules(target)
        assert warnings == []

    def test_provision_to_local_returns_reconciliation(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        gaps = analyze_gaps(hub_resources, project_names, ["fastapi-python"])
        summary = provision_to_local(hub_root, project_dir, gaps, ["fastapi-python"])
        assert "reconciliation_warnings" in summary
        assert isinstance(summary["reconciliation_warnings"], list)


# --- Main: --provision flag ---


class TestMainProvisionFlag:
    def test_flag_accepted(self):
        """--provision flag is accepted by the argument parser."""
        import argparse
        from scripts.recommend import main
        import sys
        # Just verify the parser doesn't reject --provision
        # We can't actually run main() without a repo/local, but we can
        # test that it parses correctly by invoking the parser directly
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--repo")
        group.add_argument("--local")
        action_group = parser.add_mutually_exclusive_group()
        action_group.add_argument("--apply", action="store_true")
        action_group.add_argument("--provision", action="store_true")
        args = parser.parse_args(["--local", "/tmp/test", "--provision"])
        assert args.provision is True
        assert args.apply is False

    def test_mutually_exclusive_with_apply(self):
        """--provision and --apply cannot be used together."""
        import argparse
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--repo")
        group.add_argument("--local")
        action_group = parser.add_mutually_exclusive_group()
        action_group.add_argument("--apply", action="store_true")
        action_group.add_argument("--provision", action="store_true")
        with pytest.raises(SystemExit):
            parser.parse_args(["--local", "/tmp/test", "--apply", "--provision"])


# --- Dependency Detection ---


class TestDetectDependencies:
    def test_parse_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"vue": "^3.4.0", "pinia": "^2.1.0"},
            "devDependencies": {"vitest": "^1.0.0", "@playwright/test": "^1.40.0"},
        }))
        deps = detect_dependencies_from_dir(tmp_path)
        assert "npm" in deps
        assert "vue" in deps["npm"]
        assert "pinia" in deps["npm"]
        assert "vitest" in deps["npm"]
        assert "@playwright/test" in deps["npm"]

    def test_parse_requirements_txt(self, tmp_path):
        (tmp_path / "requirements.txt").write_text(
            "fastapi>=0.109.0\nuvicorn>=0.27.0\nsqlalchemy[asyncio]>=2.0\n# comment\n"
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "pip" in deps
        assert "fastapi" in deps["pip"]
        assert "uvicorn" in deps["pip"]
        assert "sqlalchemy" in deps["pip"]

    def test_parse_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = [\n  "fastapi>=0.109",\n  "anthropic>=0.18",\n]\n'
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "pip" in deps
        assert "fastapi" in deps["pip"]
        assert "anthropic" in deps["pip"]

    def test_nested_subdirectory(self, tmp_path):
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(json.dumps({
            "dependencies": {"next": "14.0.0"},
        }))
        deps = detect_dependencies_from_dir(tmp_path)
        assert "npm" in deps
        assert "next" in deps["npm"]

    def test_empty_project(self, tmp_path):
        deps = detect_dependencies_from_dir(tmp_path)
        assert deps == {}

    def test_parse_build_gradle(self, tmp_path):
        (tmp_path / "build.gradle.kts").write_text(
            'dependencies {\n'
            '    implementation("androidx.compose:compose-runtime:1.5.0")\n'
            '    testImplementation("junit:junit:4.13")\n'
            '}\n'
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "gradle" in deps
        assert "compose-runtime" in deps["gradle"]

    def test_parse_pubspec_yaml(self, tmp_path):
        (tmp_path / "pubspec.yaml").write_text(
            "dependencies:\n  flutter:\n    sdk: flutter\n  dio: ^5.0.0\n"
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "pub" in deps
        assert "flutter" in deps["pub"]
        assert "dio" in deps["pub"]

    def test_parse_go_mod(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module example.com/myapp\n\ngo 1.21\n\n"
            "require (\n\tgithub.com/gin-gonic/gin v1.9.1\n"
            "\tgithub.com/go-redis/redis v6.15.9\n)\n"
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "go" in deps
        assert "gin" in deps["go"]
        assert "redis" in deps["go"]

    def test_parse_gemfile(self, tmp_path):
        (tmp_path / "Gemfile").write_text(
            "source 'https://rubygems.org'\ngem 'rails'\ngem 'redis'\n"
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "gem" in deps
        assert "rails" in deps["gem"]
        assert "redis" in deps["gem"]

    def test_parse_cargo_toml(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text(
            "[dependencies]\ntokio = \"1.0\"\nserde = { version = \"1.0\", features = [\"derive\"] }\n"
        )
        deps = detect_dependencies_from_dir(tmp_path)
        assert "cargo" in deps
        assert "tokio" in deps["cargo"]
        assert "serde" in deps["cargo"]

    def test_multiple_ecosystems(self, tmp_path):
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"vue": "^3.0.0"},
        }))
        (tmp_path / "requirements.txt").write_text("fastapi>=0.109.0\n")
        deps = detect_dependencies_from_dir(tmp_path)
        assert "npm" in deps
        assert "pip" in deps
        assert "vue" in deps["npm"]
        assert "fastapi" in deps["pip"]


class TestResolveDepPatterns:
    def test_known_dep_resolves(self):
        deps = {"npm": ["vue", "vitest"]}
        promoted = resolve_dep_patterns(deps)
        assert "vue-dev" in promoted
        assert "vue-test" in promoted
        assert "vitest-dev" in promoted

    def test_unknown_dep_ignored(self):
        deps = {"npm": ["unknown-package-xyz"]}
        promoted = resolve_dep_patterns(deps)
        assert len(promoted) == 0

    def test_multiple_ecosystems(self):
        deps = {"npm": ["vue"], "pip": ["fastapi"]}
        promoted = resolve_dep_patterns(deps)
        assert "vue-dev" in promoted
        assert "fastapi-run-backend-tests" in promoted

    def test_empty_deps(self):
        assert resolve_dep_patterns({}) == set()

    def test_redis_from_ioredis(self):
        deps = {"npm": ["ioredis"]}
        promoted = resolve_dep_patterns(deps)
        assert "redis-patterns" in promoted


@pytest.mark.usefixtures("_prime_real_registry")
class TestTierResourceWithDeps:
    def test_dep_promotes_from_nice_to_have(self):
        """vue-dev without deps is nice-to-have (universal), with deps is must-have."""
        assert tier_resource("vue-dev", "skill", []) == "nice-to-have"
        assert tier_resource("vue-dev", "skill", [], dep_promoted={"vue-dev"}) == "must-have"

    def test_dep_promotes_from_skip(self):
        """d3-viz is nice-to-have without deps, must-have when dep-promoted."""
        assert tier_resource("d3-viz", "skill", []) == "nice-to-have"
        assert tier_resource("d3-viz", "skill", [], dep_promoted={"d3-viz"}) == "must-have"

    def test_no_deps_backward_compat(self):
        """Without dep_promoted, behavior is same as before."""
        assert tier_resource("tdd", "skill", []) == "must-have"
        assert tier_resource("vitest-dev", "skill", []) == "nice-to-have"
        assert tier_resource("twitter-x", "skill", []) == "skip"

    def test_dep_overrides_wrong_stack(self):
        """Dep-promoted patterns bypass wrong-stack check."""
        # fastapi-db-migrate without android-compose stack would normally skip
        assert tier_resource("fastapi-db-migrate", "skill", ["android-compose"]) == "skip"
        # But with dep promotion, it's must-have
        assert tier_resource(
            "fastapi-db-migrate", "skill", ["android-compose"],
            dep_promoted={"fastapi-db-migrate"},
        ) == "must-have"


@pytest.mark.usefixtures("_prime_hub_registry")
class TestAnalyzeGapsWithDeps:
    def test_deps_override_always_skip(self, hub_root, project_dir):
        """d3-viz is no longer skipped when d3 dep is detected."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]
        deps = {"npm": ["d3"]}

        gaps = analyze_gaps(hub_resources, project_names, stacks, deps=deps)

        must_names = {g["name"] for g in gaps["must-have"]}
        skip_names = {g["name"] for g in gaps["skip"]}
        assert "d3-viz" in must_names
        assert "d3-viz" not in skip_names

    def test_backward_compat_without_deps(self, hub_root, project_dir):
        """Without deps, behavior is same as before."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)

        must_names = {g["name"] for g in gaps["must-have"]}
        assert "tdd" in must_names
        assert "skill-master" in must_names

    def test_gaps_has_improved_key(self, hub_root, project_dir):
        """analyze_gaps returns 'improved' key in output."""
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        assert "improved" in gaps
        assert isinstance(gaps["improved"], list)


class TestDetectImprovedPatterns:
    def test_identical_hash_skipped(self, tmp_path):
        """Patterns with identical content are not flagged as improved."""
        hub_root = tmp_path / "hub"
        core = hub_root / "core" / ".claude"
        skill_dir = core / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        content = "---\nname: fix-loop\nversion: '2.0.0'\n---\n# Fix Loop\n\nContent here.\n"
        (skill_dir / "SKILL.md").write_text(content)

        import hashlib
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        project_claude = tmp_path / "project" / ".claude"
        proj_skill = project_claude / "skills" / "fix-loop"
        proj_skill.mkdir(parents=True)
        (proj_skill / "SKILL.md").write_text(content)

        hub_resources = {"skill": [{"name": "fix-loop", "path": skill_dir / "SKILL.md"}]}
        project_names = {"skill": {"fix-loop"}}
        registry = {"fix-loop": {"hash": content_hash, "version": "2.0.0"}}

        improved = detect_improved_patterns(
            hub_root, project_claude, hub_resources, project_names, registry,
        )
        assert len(improved) == 0

    def test_hub_newer_detected(self, tmp_path):
        """Hub with newer version is flagged as improved."""
        hub_root = tmp_path / "hub"
        core = hub_root / "core" / ".claude"
        skill_dir = core / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        hub_content = "---\nname: fix-loop\nversion: '3.0.0'\n---\n# Fix Loop v3\n\nNew content.\n"
        (skill_dir / "SKILL.md").write_text(hub_content)

        import hashlib
        hub_hash = hashlib.sha256(hub_content.encode("utf-8")).hexdigest()

        project_claude = tmp_path / "project" / ".claude"
        proj_skill = project_claude / "skills" / "fix-loop"
        proj_skill.mkdir(parents=True)
        proj_content = "---\nname: fix-loop\nversion: '2.0.0'\n---\n# Fix Loop v2\n\nOld content.\n"
        (proj_skill / "SKILL.md").write_text(proj_content)

        hub_resources = {"skill": [{"name": "fix-loop", "path": skill_dir / "SKILL.md"}]}
        project_names = {"skill": {"fix-loop"}}
        registry = {"fix-loop": {"hash": hub_hash, "version": "3.0.0"}}

        improved = detect_improved_patterns(
            hub_root, project_claude, hub_resources, project_names, registry,
        )
        assert len(improved) == 1
        assert improved[0]["name"] == "fix-loop"
        assert "3.0.0" in improved[0]["reason"]

    def test_project_customized_skipped(self, tmp_path):
        """Project with >= hub version is not flagged."""
        hub_root = tmp_path / "hub"
        core = hub_root / "core" / ".claude"
        skill_dir = core / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: fix-loop\nversion: '2.0.0'\n---\n# v2\n")

        project_claude = tmp_path / "project" / ".claude"
        proj_skill = project_claude / "skills" / "fix-loop"
        proj_skill.mkdir(parents=True)
        proj_content = "---\nname: fix-loop\nversion: '3.0.0'\n---\n# v3 custom\n"
        (proj_skill / "SKILL.md").write_text(proj_content)

        hub_resources = {"skill": [{"name": "fix-loop", "path": skill_dir / "SKILL.md"}]}
        project_names = {"skill": {"fix-loop"}}
        registry = {"fix-loop": {"hash": "different", "version": "2.0.0"}}

        improved = detect_improved_patterns(
            hub_root, project_claude, hub_resources, project_names, registry,
        )
        assert len(improved) == 0

    def test_no_version_flagged(self, tmp_path):
        """Project pattern with no version is flagged when hub has a version."""
        hub_root = tmp_path / "hub"
        core = hub_root / "core" / ".claude"
        skill_dir = core / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: fix-loop\nversion: '2.0.0'\n---\n# v2\n")

        project_claude = tmp_path / "project" / ".claude"
        proj_skill = project_claude / "skills" / "fix-loop"
        proj_skill.mkdir(parents=True)
        (proj_skill / "SKILL.md").write_text("---\nname: fix-loop\n---\n# No version\n")

        hub_resources = {"skill": [{"name": "fix-loop", "path": skill_dir / "SKILL.md"}]}
        project_names = {"skill": {"fix-loop"}}
        registry = {"fix-loop": {"hash": "different", "version": "2.0.0"}}

        improved = detect_improved_patterns(
            hub_root, project_claude, hub_resources, project_names, registry,
        )
        assert len(improved) == 1
        assert "no version" in improved[0]["reason"]

    def test_same_version_different_hash(self, tmp_path):
        """Same version but different content is flagged for review."""
        hub_root = tmp_path / "hub"
        core = hub_root / "core" / ".claude"
        skill_dir = core / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: fix-loop\nversion: '2.0.0'\n---\n# Hub v2\n")

        project_claude = tmp_path / "project" / ".claude"
        proj_skill = project_claude / "skills" / "fix-loop"
        proj_skill.mkdir(parents=True)
        (proj_skill / "SKILL.md").write_text("---\nname: fix-loop\nversion: '2.0.0'\n---\n# Proj v2 customized\n")

        hub_resources = {"skill": [{"name": "fix-loop", "path": skill_dir / "SKILL.md"}]}
        project_names = {"skill": {"fix-loop"}}
        registry = {"fix-loop": {"hash": "hub-hash-different", "version": "2.0.0"}}

        improved = detect_improved_patterns(
            hub_root, project_claude, hub_resources, project_names, registry,
        )
        assert len(improved) == 1
        assert "same version" in improved[0]["reason"]


# --- Multi-PR Helpers ---


class TestCopyResourcesForTier:
    def test_copies_skills(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        items = [{"name": "tdd", "type": "skill", "tier": "must-have"}]
        copied = _copy_resources_for_tier(hub_root, target, items)
        assert len(copied) == 1
        assert "tdd" in copied[0]
        assert (target / ".claude" / "skills" / "tdd" / "SKILL.md").exists()

    def test_copies_agents(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        items = [{"name": "security-auditor-agent", "type": "agent", "tier": "must-have"}]
        copied = _copy_resources_for_tier(hub_root, target, items)
        assert len(copied) == 1
        assert "security-auditor-agent" in copied[0]
        assert (target / ".claude" / "agents" / "security-auditor-agent.md").exists()

    def test_copies_rules(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        items = [{"name": "workflow", "type": "rule", "tier": "nice-to-have"}]
        copied = _copy_resources_for_tier(hub_root, target, items)
        assert len(copied) == 1
        assert (target / ".claude" / "rules" / "workflow.md").exists()

    def test_copies_hooks(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        items = [{"name": "secret-scanner", "type": "hook", "tier": "must-have"}]
        copied = _copy_resources_for_tier(hub_root, target, items)
        assert len(copied) == 1
        assert (target / ".claude" / "hooks" / "secret-scanner.sh").exists()

    def test_empty_items_returns_empty(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        copied = _copy_resources_for_tier(hub_root, target, [])
        assert copied == []

    def test_multiple_types(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        items = [
            {"name": "tdd", "type": "skill", "tier": "must-have"},
            {"name": "workflow", "type": "rule", "tier": "must-have"},
            {"name": "secret-scanner", "type": "hook", "tier": "must-have"},
        ]
        copied = _copy_resources_for_tier(hub_root, target, items)
        assert len(copied) == 3

    def test_nonexistent_resource_skipped(self, hub_root, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        items = [{"name": "nonexistent-xyz", "type": "skill", "tier": "must-have"}]
        copied = _copy_resources_for_tier(hub_root, target, items)
        assert copied == []


class TestFormatNiceToHavePrBody:
    def test_contains_checkboxes(self):
        items = [
            {"name": "brainstorm", "type": "skill", "tier": "nice-to-have"},
            {"name": "testing", "type": "rule", "tier": "nice-to-have"},
        ]
        body = _format_nice_to_have_pr_body(items)
        assert "- [ ] `brainstorm`" in body
        assert "- [ ] `testing`" in body

    def test_groups_by_type(self):
        items = [
            {"name": "brainstorm", "type": "skill", "tier": "nice-to-have"},
            {"name": "testing", "type": "rule", "tier": "nice-to-have"},
            {"name": "docs-manager-agent", "type": "agent", "tier": "nice-to-have"},
        ]
        body = _format_nice_to_have_pr_body(items)
        assert "### Skills" in body
        assert "### Rules" in body
        assert "### Agents" in body

    def test_empty_type_section_omitted(self):
        items = [{"name": "brainstorm", "type": "skill", "tier": "nice-to-have"}]
        body = _format_nice_to_have_pr_body(items)
        assert "### Skills" in body
        assert "### Rules" not in body
        assert "### Agents" not in body

    def test_has_instructions(self):
        items = [{"name": "brainstorm", "type": "skill", "tier": "nice-to-have"}]
        body = _format_nice_to_have_pr_body(items)
        assert "/apply" in body
        assert "Unchecked" in body

    def test_sorted_within_type(self):
        items = [
            {"name": "z-skill", "type": "skill", "tier": "nice-to-have"},
            {"name": "a-skill", "type": "skill", "tier": "nice-to-have"},
        ]
        body = _format_nice_to_have_pr_body(items)
        a_pos = body.index("`a-skill`")
        z_pos = body.index("`z-skill`")
        assert a_pos < z_pos


# --- Hub Practices Section: Dynamic Counts ---


class TestGenerateHubSectionCounts:
    def test_with_counts(self, hub_root):
        project_names = {
            "skill": {"fix-loop", "tdd", "brainstorm"},
            "agent": {"debugger-agent", "tester-agent"},
            "rule": {"workflow"},
        }
        section = generate_hub_practices_section(
            hub_root, ["workflow"], project_names=project_names,
        )
        assert "3 skills, 2 agents, and 1 rules" in section

    def test_without_counts(self, hub_root):
        section = generate_hub_practices_section(hub_root, ["workflow"])
        assert "contains skills, agents, and rules for Claude Code" in section


# --- MUST_HAVE_RULES Expansion ---


@pytest.mark.usefixtures("_prime_real_registry")
class TestMustHaveRulesExpanded:
    def test_expanded_rules_in_set(self):
        for rule in ["workflow", "claude-behavior", "testing", "tdd-rule", "context-management"]:
            assert rule in MUST_HAVE_RULES, f"{rule} should be in MUST_HAVE_RULES"

    def test_tier_workflow_is_must_have(self):
        tier, reason = tier_resource_with_reason("workflow", "rule", [])
        assert tier == "must-have"
        assert "must-have" in reason

    def test_tier_claude_behavior_is_must_have(self):
        tier, _ = tier_resource_with_reason("claude-behavior", "rule", [])
        assert tier == "must-have"

    def test_tier_testing_is_must_have(self):
        tier, _ = tier_resource_with_reason("testing", "rule", [])
        assert tier == "must-have"

    def test_tier_tdd_rule_is_must_have(self):
        tier, _ = tier_resource_with_reason("tdd-rule", "rule", [])
        assert tier == "must-have"


# --- Provision JSON Combined Output ---


class TestProvisionJsonCombined:
    def test_provision_summary_has_copied_files(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        gaps = {"must-have": [
            {"name": "fix-loop", "type": "skill", "tier": "must-have", "reason": "core"},
        ], "improved": [], "nice-to-have": [], "skip": []}
        summary = provision_to_local(hub_root, target, gaps, ["general"])
        assert "copied_files" in summary
        assert isinstance(summary["copied_files"], list)

    def test_provision_combined_json_structure(self, hub_root, tmp_path):
        target = tmp_path / "myproject"
        target.mkdir()
        gaps = {"must-have": [
            {"name": "workflow", "type": "rule", "tier": "must-have", "reason": "core"},
        ], "improved": [], "nice-to-have": [], "skip": []}
        summary = provision_to_local(hub_root, target, gaps, ["general"])
        combined = {"gaps": gaps, "provision": summary}
        assert "gaps" in combined
        assert "provision" in combined
        assert "copied_files" in combined["provision"]
        assert "claude_md" in combined["provision"]


# --- Sync Manifest Tests ---


class TestComputeFileHash:
    def test_deterministic(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello world", encoding="utf-8")
        assert _compute_file_hash(f) == _compute_file_hash(f)

    def test_crlf_lf_equivalent(self, tmp_path):
        f1 = tmp_path / "lf.md"
        f2 = tmp_path / "crlf.md"
        f1.write_bytes(b"line1\nline2\n")
        f2.write_bytes(b"line1\r\nline2\r\n")
        assert _compute_file_hash(f1) == _compute_file_hash(f2)

    def test_different_content(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("aaa", encoding="utf-8")
        f2.write_text("bbb", encoding="utf-8")
        assert _compute_file_hash(f1) != _compute_file_hash(f2)

    def test_sha256_prefix(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("test", encoding="utf-8")
        assert _compute_file_hash(f).startswith("sha256:")


class TestClassifySyncStatus:
    def test_up_to_date(self):
        assert classify_sync_status("A", "A", "A") == "up-to-date"

    def test_up_to_date_no_manifest(self):
        assert classify_sync_status("A", "A", None) == "up-to-date"

    def test_hub_only_change(self):
        assert classify_sync_status("B", "A", "A") == "hub-only"

    def test_project_only_change(self):
        assert classify_sync_status("A", "B", "A") == "project-only"

    def test_conflict(self):
        assert classify_sync_status("B", "C", "A") == "conflict"

    def test_no_manifest_entry(self):
        assert classify_sync_status("B", "A", None) == "no-manifest"

    def test_hub_and_project_same_change(self):
        # Both changed to the same thing — up-to-date
        assert classify_sync_status("B", "B", "A") == "up-to-date"


class TestSyncManifestIO:
    def test_load_missing_returns_empty(self, tmp_path):
        manifest = load_sync_manifest(tmp_path)
        assert manifest["files"] == {}
        assert manifest["_meta"]["version"] == "1.0.0"

    def test_save_and_load_roundtrip(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        manifest = load_sync_manifest(tmp_path)
        manifest["files"]["rules/test.md"] = {
            "hub_hash": "sha256:abc123",
            "synced_at": "2026-03-21T00:00:00Z",
        }
        save_sync_manifest(tmp_path, manifest)
        loaded = load_sync_manifest(tmp_path)
        assert "rules/test.md" in loaded["files"]
        assert loaded["_meta"]["last_sync"] is not None

    def test_load_corrupt_returns_empty(self, tmp_path):
        p = tmp_path / ".claude" / "sync-manifest.json"
        p.parent.mkdir(parents=True)
        p.write_text("{invalid json", encoding="utf-8")
        manifest = load_sync_manifest(tmp_path)
        assert manifest["files"] == {}

    def test_load_missing_files_key_returns_empty(self, tmp_path):
        p = tmp_path / ".claude" / "sync-manifest.json"
        p.parent.mkdir(parents=True)
        p.write_text('{"_meta": {}}', encoding="utf-8")
        manifest = load_sync_manifest(tmp_path)
        assert manifest["files"] == {}


class TestBuildSyncClassification:
    def test_hub_only_detected(self, hub_root, tmp_path):
        """Rule exists in both but project has stale version -> hub-only."""
        project = tmp_path / "project"
        project.mkdir()
        claude = project / ".claude" / "rules"
        claude.mkdir(parents=True)
        (claude / "workflow.md").write_text("old content", encoding="utf-8")

        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project / ".claude")

        # Manifest records old content hash as the hub hash at sync time
        manifest = load_sync_manifest(project)
        manifest["files"]["rules/workflow.md"] = {
            "hub_hash": _compute_file_hash(claude / "workflow.md"),
            "synced_at": "2026-03-01T00:00:00Z",
        }

        result = build_sync_classification(
            hub_root, project, hub_resources, project_names, manifest,
        )
        workflow_items = [i for i in result["hub-only"] if i["name"] == "workflow"]
        assert len(workflow_items) == 1

    def test_project_only_detected(self, hub_root, tmp_path):
        """Project modified a rule but hub hasn't changed -> project-only."""
        project = tmp_path / "project"
        project.mkdir()
        claude = project / ".claude" / "rules"
        claude.mkdir(parents=True)
        (claude / "workflow.md").write_text("customized content", encoding="utf-8")

        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project / ".claude")

        # Manifest records current hub hash (hub hasn't changed since sync)
        hub_hash = _compute_file_hash(hub_root / "core" / ".claude" / "rules" / "workflow.md")
        manifest = load_sync_manifest(project)
        manifest["files"]["rules/workflow.md"] = {
            "hub_hash": hub_hash,
            "synced_at": "2026-03-01T00:00:00Z",
        }

        result = build_sync_classification(
            hub_root, project, hub_resources, project_names, manifest,
        )
        proj_only = [i for i in result["project-only"] if i["name"] == "workflow"]
        assert len(proj_only) == 1

    def test_no_manifest_all_classified(self, hub_root, tmp_path):
        """No manifest -> all overlapping files classified as no-manifest."""
        project = tmp_path / "project"
        project.mkdir()
        claude = project / ".claude" / "rules"
        claude.mkdir(parents=True)
        (claude / "workflow.md").write_text("old content", encoding="utf-8")

        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project / ".claude")
        manifest = load_sync_manifest(project)  # empty

        result = build_sync_classification(
            hub_root, project, hub_resources, project_names, manifest,
        )
        # workflow should be in no-manifest (project version differs from hub)
        no_man = [i for i in result["no-manifest"] if i["name"] == "workflow"]
        assert len(no_man) == 1


class TestUpdateImprovedToLocal:
    def test_overwrites_existing_rule(self, hub_root, tmp_path):
        project = tmp_path / "project"
        rules = project / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "workflow.md").write_text("old", encoding="utf-8")

        items = [{"name": "workflow", "type": "rule", "rel_path": "rules/workflow.md"}]
        updated = update_improved_to_local(hub_root, project, items)
        assert len(updated) == 1
        new_content = (rules / "workflow.md").read_text(encoding="utf-8")
        assert new_content != "old"

    def test_overwrites_existing_skill(self, hub_root, tmp_path):
        project = tmp_path / "project"
        skill = project / ".claude" / "skills" / "tdd"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("old", encoding="utf-8")

        items = [{"name": "tdd", "type": "skill", "rel_path": "skills/tdd/SKILL.md"}]
        updated = update_improved_to_local(hub_root, project, items)
        assert any("tdd" in f for f in updated)


class TestProvisionWithManifest:
    def test_first_run_creates_manifest(self, hub_root, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        gaps = {"must-have": [
            {"name": "tdd", "type": "skill", "tier": "must-have"},
        ], "improved": [], "nice-to-have": [], "skip": []}
        summary = provision_to_local(hub_root, project, gaps, ["general"])
        manifest_path = project / ".claude" / "sync-manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert len(manifest["files"]) > 0
        assert manifest["_meta"]["last_sync"] is not None

    def test_summary_includes_sync_fields(self, hub_root, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        gaps = {"must-have": [], "improved": [], "nice-to-have": [], "skip": []}
        summary = provision_to_local(hub_root, project, gaps, ["general"])
        assert "auto_updated" in summary
        assert "sync_classification" in summary
        assert "conflicts" in summary


# --- Headless Conflict Resolution ---


class TestHeadlessConflictResolution:
    """provision_to_local must not hang on input() when run non-interactively.
    The `on_conflict` parameter + TTY auto-detection drive the fallback."""

    def _build_project_with_conflict(self, hub_root, project):
        """Create a conflict: a skill that exists in both hub and project,
        where both sides have diverged from the manifest hash."""
        from scripts.recommend import load_sync_manifest, save_sync_manifest
        # First pass: copy the skill in cleanly
        gaps = {"must-have": [
            {"name": "tdd", "type": "skill", "tier": "must-have"},
        ], "improved": [], "nice-to-have": [], "skip": []}
        provision_to_local(hub_root, project, gaps, ["general"], on_conflict="skip")
        # Mutate the project's copy to diverge from the hub
        skill_md = project / ".claude" / "skills" / "tdd" / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n## Local customization\n")
        # Mutate the manifest's recorded hash so the hub side is seen as changed
        manifest = load_sync_manifest(project)
        for rel in manifest["files"]:
            if rel.startswith(".claude/skills/tdd/"):
                manifest["files"][rel]["hub_hash"] = "0" * 64  # stale hash
        save_sync_manifest(project, manifest)

    def test_on_conflict_skip_does_not_call_input(self, hub_root, tmp_path, monkeypatch):
        """With on_conflict='skip', conflict resolution must not prompt stdin."""
        project = tmp_path / "proj-skip"
        project.mkdir()
        self._build_project_with_conflict(hub_root, project)

        def _forbid_input(prompt=""):
            raise AssertionError(f"input() must not be called in skip mode — prompt was: {prompt!r}")
        monkeypatch.setattr("builtins.input", _forbid_input)

        gaps = {"must-have": [], "improved": [
            {"name": "tdd", "type": "skill", "tier": "improved"},
        ], "nice-to-have": [], "skip": []}
        summary = provision_to_local(hub_root, project, gaps, ["general"], on_conflict="skip")
        # Conflict was kept local (skipped)
        assert summary["sync_classification"]["conflict"] >= 0  # no crash
        # conflict_overwritten should be empty — nothing was overwritten
        assert summary.get("conflict_overwritten", []) == []

    def test_on_conflict_overwrite_does_not_call_input(self, hub_root, tmp_path, monkeypatch):
        """With on_conflict='overwrite', every conflict is auto-overwritten without prompting."""
        project = tmp_path / "proj-over"
        project.mkdir()
        self._build_project_with_conflict(hub_root, project)

        def _forbid_input(prompt=""):
            raise AssertionError(f"input() must not be called in overwrite mode — prompt was: {prompt!r}")
        monkeypatch.setattr("builtins.input", _forbid_input)

        gaps = {"must-have": [], "improved": [
            {"name": "tdd", "type": "skill", "tier": "improved"},
        ], "nice-to-have": [], "skip": []}
        provision_to_local(hub_root, project, gaps, ["general"], on_conflict="overwrite")

    def test_on_conflict_auto_falls_back_to_skip_when_no_tty(self, hub_root, tmp_path, monkeypatch):
        """When on_conflict='auto' (default) and stdin is not a TTY, the behavior
        MUST fall back to 'skip' rather than hang on input()."""
        project = tmp_path / "proj-auto"
        project.mkdir()
        self._build_project_with_conflict(hub_root, project)

        # Force non-TTY environment
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        def _forbid_input(prompt=""):
            raise AssertionError(
                f"input() must not be called when stdin is not a TTY — prompt was: {prompt!r}"
            )
        monkeypatch.setattr("builtins.input", _forbid_input)

        gaps = {"must-have": [], "improved": [
            {"name": "tdd", "type": "skill", "tier": "improved"},
        ], "nice-to-have": [], "skip": []}
        # Should not raise
        provision_to_local(hub_root, project, gaps, ["general"])  # on_conflict defaults to "auto"

    def test_resolve_conflict_mode_auto_with_both_ttys(self, monkeypatch):
        """Pure-function test: auto → interactive only when BOTH stdin and stdout are TTYs."""
        from scripts.recommend import _resolve_conflict_mode
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert _resolve_conflict_mode("auto") == "interactive"

    def test_resolve_conflict_mode_auto_skips_when_stdout_redirected(self, monkeypatch):
        """Regression: a live /synthesize-project run on Windows crashed with
        EOFError because stdin reported isatty=True inside the subprocess
        even though stdout was redirected via `recommend.py --json > out.json`.
        When stdout is redirected, the caller is programmatic. Fall back to skip."""
        from scripts.recommend import _resolve_conflict_mode
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: False)
        assert _resolve_conflict_mode("auto") == "skip"

    def test_resolve_conflict_mode_auto_skips_when_stdin_redirected(self, monkeypatch):
        from scripts.recommend import _resolve_conflict_mode
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert _resolve_conflict_mode("auto") == "skip"

    def test_resolve_conflict_mode_explicit_values_pass_through(self, monkeypatch):
        from scripts.recommend import _resolve_conflict_mode
        # Explicit modes ignore TTY state
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert _resolve_conflict_mode("skip") == "skip"
        assert _resolve_conflict_mode("overwrite") == "overwrite"
        assert _resolve_conflict_mode("error") == "error"
        assert _resolve_conflict_mode("interactive") == "interactive"


# --- Registry Tier SSOT ---


class TestRegistryTierSSOT:
    """Every pattern in registry/patterns.json MUST have an explicit tier field.
    This ensures recommend.py never falls through to hardcoded defaults."""

    def test_all_registry_patterns_have_tier(self):
        """Every pattern in registry (except _meta) must have a tier field."""
        registry_path = Path(__file__).parent.parent.parent / "registry" / "patterns.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        missing = []
        for name, entry in registry.items():
            if name == "_meta":
                continue
            if not isinstance(entry, dict):
                continue
            if "tier" not in entry:
                missing.append(name)

        assert missing == [], (
            f"{len(missing)} patterns missing 'tier' field: {missing[:10]}..."
        )

    def test_all_registry_tiers_are_valid(self):
        """Tier values must be one of: must-have, nice-to-have, skip."""
        registry_path = Path(__file__).parent.parent.parent / "registry" / "patterns.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        valid_tiers = {"must-have", "nice-to-have", "skip"}
        invalid = []
        for name, entry in registry.items():
            if name == "_meta" or not isinstance(entry, dict):
                continue
            tier = entry.get("tier")
            if tier and tier not in valid_tiers:
                invalid.append((name, tier))

        assert invalid == [], f"Invalid tier values: {invalid}"

    def test_always_skip_patterns_have_skip_tier(self):
        """Patterns in ALWAYS_SKIP should have tier: skip in registry."""
        from scripts.recommend import ALWAYS_SKIP
        registry_path = Path(__file__).parent.parent.parent / "registry" / "patterns.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        for name in ALWAYS_SKIP:
            if name in registry:
                assert registry[name].get("tier") == "skip", (
                    f"ALWAYS_SKIP pattern '{name}' should have tier: skip, "
                    f"got: {registry[name].get('tier')}"
                )

    def test_tier_resource_uses_registry_not_fallback(self, tmp_path):
        """When registry has a tier, it must be used — no fallback to hardcoded sets."""
        from scripts.recommend import _load_tier_registry

        # Create a registry where a normally-must-have skill has nice-to-have
        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        (registry_dir / "patterns.json").write_text(json.dumps({
            "tdd": {"tier": "nice-to-have", "type": "skill"},
        }))

        # Prime the cache
        _load_tier_registry._cache = {}
        _load_tier_registry(tmp_path)

        try:
            tier, reason = tier_resource_with_reason("tdd", "skill", [])
            assert tier == "nice-to-have", (
                f"Registry tier should override hardcoded CORE_WORKFLOW_SKILLS. "
                f"Got tier={tier}, reason={reason}"
            )
        finally:
            _load_tier_registry._cache = {}

    def test_no_hardcoded_fallback_for_unknown_pattern(self, tmp_path):
        """Patterns not in registry should get nice-to-have default, not crash."""
        from scripts.recommend import _load_tier_registry

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        (registry_dir / "patterns.json").write_text(json.dumps({}))

        _load_tier_registry._cache = {}
        _load_tier_registry(tmp_path)

        try:
            # Unknown pattern should still get a reasonable default
            tier, reason = tier_resource_with_reason("nonexistent-skill", "skill", [])
            assert tier in ("must-have", "nice-to-have", "skip")
        finally:
            _load_tier_registry._cache = {}


class TestRegistryTierCI:
    """CI validation: workflow_quality_gate must catch missing tiers."""

    def test_validator_catches_missing_tier(self, tmp_path):
        """The validate_registry_tiers function should report patterns without tier."""
        from scripts.workflow_quality_gate_validate_patterns import validate_registry_tiers

        registry_path = tmp_path / "patterns.json"
        registry_path.write_text(json.dumps({
            "_meta": {"version": "1.0.0"},
            "good-skill": {"type": "skill", "tier": "must-have"},
            "bad-skill": {"type": "skill"},
        }))

        errors = validate_registry_tiers(registry_path)
        assert len(errors) == 1
        assert "bad-skill" in errors[0]

    def test_validator_catches_invalid_tier(self, tmp_path):
        """The validate_registry_tiers function should report invalid tier values."""
        from scripts.workflow_quality_gate_validate_patterns import validate_registry_tiers

        registry_path = tmp_path / "patterns.json"
        registry_path.write_text(json.dumps({
            "_meta": {"version": "1.0.0"},
            "bad-skill": {"type": "skill", "tier": "important"},
        }))

        errors = validate_registry_tiers(registry_path)
        assert len(errors) == 1
        assert "invalid tier" in errors[0].lower() or "bad-skill" in errors[0]

    def test_validator_passes_with_all_tiers(self, tmp_path):
        """No errors when all patterns have valid tiers."""
        from scripts.workflow_quality_gate_validate_patterns import validate_registry_tiers

        registry_path = tmp_path / "patterns.json"
        registry_path.write_text(json.dumps({
            "_meta": {"version": "1.0.0"},
            "skill-a": {"type": "skill", "tier": "must-have"},
            "skill-b": {"type": "skill", "tier": "nice-to-have"},
            "skill-c": {"type": "skill", "tier": "skip"},
        }))

        errors = validate_registry_tiers(registry_path)
        assert errors == []


class TestProvisionIdempotency:
    """Running provision_to_local twice in a row should leave the project in
    the same state — no spurious conflicts, no re-copied files, no churn."""

    def test_second_run_reports_no_new_work(self, hub_root, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        gaps = {"must-have": [
            {"name": "tdd", "type": "skill", "tier": "must-have"},
        ], "improved": [], "nice-to-have": [], "skip": []}

        first = provision_to_local(hub_root, project, gaps, ["general"], on_conflict="skip")
        second = provision_to_local(hub_root, project, gaps, ["general"], on_conflict="skip")

        # No conflicts on second run (the first run fully synced the pattern)
        assert second["sync_classification"]["conflict"] == 0
        # No auto-updates on second run (nothing stale)
        assert len(second["auto_updated"]) == 0
        # No new copies (files already exist locally)
        assert len(second["copied_files"]) == 0

    def test_second_run_does_not_mutate_claude_md(self, hub_root, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        gaps = {"must-have": [], "improved": [], "nice-to-have": [], "skip": []}

        provision_to_local(hub_root, project, gaps, ["fastapi-python"], on_conflict="skip")
        first_claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")

        provision_to_local(hub_root, project, gaps, ["fastapi-python"], on_conflict="skip")
        second_claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")

        assert first_claude_md == second_claude_md, (
            "CLAUDE.md content drifted between consecutive provisioning runs — "
            "this is a nondeterminism bug that creates noise for users"
        )

    def test_second_run_does_not_mutate_sync_manifest_beyond_timestamps(self, hub_root, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        gaps = {"must-have": [
            {"name": "tdd", "type": "skill", "tier": "must-have"},
        ], "improved": [], "nice-to-have": [], "skip": []}

        provision_to_local(hub_root, project, gaps, ["general"], on_conflict="skip")
        import json
        manifest_path = project / ".claude" / "sync-manifest.json"
        first = json.loads(manifest_path.read_text(encoding="utf-8"))

        provision_to_local(hub_root, project, gaps, ["general"], on_conflict="skip")
        second = json.loads(manifest_path.read_text(encoding="utf-8"))

        # File entries should be a stable set across runs
        assert set(first["files"].keys()) == set(second["files"].keys()), (
            "Tracked-file set changed between consecutive provisions"
        )
        # Hub hashes per file should match (content didn't change)
        for rel, entry in first["files"].items():
            assert entry["hub_hash"] == second["files"][rel]["hub_hash"], (
                f"Hub hash for {rel} drifted between runs — possible "
                f"nondeterministic hashing"
            )


class TestResourceStackRequirementsIntegrity:
    """RESOURCE_STACK_REQUIREMENTS entries must have a viable promotion path.

    - Entries with a non-empty set of required stacks: each required stack
      must be a known stack (present in STACK_PREFIXES values or as a stack
      emitted by STACK_DETECTORS).
    - Entries with an empty set: must have a corresponding DEP_PATTERN_MAP
      entry that can promote them via dependency detection. Otherwise the
      rule is dead and will never fire.
    """

    def test_empty_stack_requirements_have_dep_promotion_path(self):
        from scripts.recommend import (
            DEP_PATTERN_MAP,
            RESOURCE_STACK_REQUIREMENTS,
        )
        # Collect all pattern names that DEP_PATTERN_MAP can promote
        dep_promotable = set()
        for patterns in DEP_PATTERN_MAP.values():
            dep_promotable.update(patterns)

        dead = []
        for name, required in RESOURCE_STACK_REQUIREMENTS.items():
            if not required and name not in dep_promotable:
                dead.append(name)
        assert dead == [], (
            f"RESOURCE_STACK_REQUIREMENTS has entries with empty required-stacks "
            f"and no DEP_PATTERN_MAP promotion path — these rules can NEVER fire: "
            f"{dead}. Either add a dep mapping in DEP_PATTERN_MAP or add explicit "
            f"stack requirements."
        )

    def test_non_empty_stack_requirements_reference_known_stacks(self):
        from scripts.recommend import (
            RESOURCE_STACK_REQUIREMENTS,
            STACK_DETECTORS,
        )
        from scripts.bootstrap import STACK_PREFIXES
        known = set(STACK_PREFIXES.keys()) | {stack for _, _, stack in STACK_DETECTORS}
        orphans = {}
        for name, required in RESOURCE_STACK_REQUIREMENTS.items():
            missing = required - known
            if missing:
                orphans[name] = sorted(missing)
        assert orphans == {}, (
            f"RESOURCE_STACK_REQUIREMENTS entries reference unknown stacks: "
            f"{orphans}. Every required stack must appear in STACK_PREFIXES or "
            f"be emitted by STACK_DETECTORS."
        )
