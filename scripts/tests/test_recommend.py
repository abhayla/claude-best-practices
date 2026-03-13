"""Tests for project resource recommendation engine."""

import json
from pathlib import Path

import pytest

from scripts.recommend import (
    analyze_gaps,
    analyze_overlaps_local,
    apply_to_local,
    classify_divergence,
    detect_stacks_from_dir,
    format_diff_report,
    format_report,
    get_hub_resources,
    get_project_resource_names,
    is_stack_specific,
    matches_stacks,
    name_matches_existing,
    tier_resource,
    _compute_line_overlap,
    _find_matching_project_name,
)


# --- Fixtures ---


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
    for name in ["debugger", "tester", "security-auditor", "fastapi-api-tester"]:
        (agents / f"{name}.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Rules
    rules = core / "rules"
    rules.mkdir(parents=True)
    for name in ["workflow", "context-management", "rule-writing-meta", "fastapi-backend"]:
        (rules / f"{name}.md").write_text(f"---\nname: {name}\n---\n# {name}")

    # Hooks
    hooks = core / "hooks"
    hooks.mkdir(parents=True)
    for name in ["dangerous-command-blocker", "secret-scanner", "auto-format"]:
        (hooks / f"{name}.sh").write_text(f"#!/bin/bash\n# {name}")

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
    for name in ["debugger", "tester", "api-tester"]:
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
        assert len(resources["rule"]) == 4
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
        assert "debugger" in names["agent"]
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
        assert name_matches_existing("fastapi-api-tester", {"api-tester", "debugger"})

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
        assert tier_resource("brainstorm", "skill", []) == "nice-to-have"
        assert tier_resource("branching", "skill", []) == "nice-to-have"

    def test_skip_always_skip_list(self):
        assert tier_resource("d3-viz", "skill", []) == "skip"
        assert tier_resource("twitter-x", "skill", []) == "skip"

    def test_skip_wrong_stack(self):
        assert tier_resource("fastapi-db-migrate", "skill", ["android-compose"]) == "skip"

    def test_must_have_rule(self):
        assert tier_resource("context-management", "rule", []) == "must-have"
        assert tier_resource("rule-writing-meta", "rule", []) == "must-have"

    def test_must_have_agent(self):
        assert tier_resource("security-auditor", "agent", []) == "must-have"

    def test_stack_override_nice_to_have(self):
        """firebase-data-connect is stack-specific but overridden to nice-to-have."""
        assert tier_resource("firebase-data-connect", "skill", ["firebase-auth"]) == "nice-to-have"

    def test_must_have_pg_query(self):
        assert tier_resource("pg-query", "skill", []) == "must-have"

    def test_must_have_compose_ui(self):
        assert tier_resource("compose-ui", "skill", []) == "must-have"


# --- Gap Analysis ---


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
        assert "debugger" not in all_names
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

    def test_skips_d3_viz(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)

        skip_names = {g["name"] for g in gaps["skip"]}
        assert "d3-viz" in skip_names


# --- Report ---


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

    def test_nice_to_have_tier_includes_both(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        must_only = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        # Reset project dir for second test
        import shutil
        shutil.rmtree(project_dir / ".claude" / "skills" / "tdd", ignore_errors=True)

        both = apply_to_local(hub_root, project_dir, gaps, tier="nice-to-have")
        assert len(both) >= len(must_only)

    def test_copies_agents(self, hub_root, project_dir):
        hub_resources = get_hub_resources(hub_root)
        project_names = get_project_resource_names(project_dir / ".claude")
        stacks = ["fastapi-python"]

        gaps = analyze_gaps(hub_resources, project_names, stacks)
        copied = apply_to_local(hub_root, project_dir, gaps, tier="must-have")

        assert any("security-auditor" in f for f in copied)
        assert (project_dir / ".claude" / "agents" / "security-auditor.md").exists()

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

        debugger = [o for o in overlaps if o["hub_name"] == "debugger"]
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
