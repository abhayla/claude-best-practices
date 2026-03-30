"""Tests for the pattern quality validator."""

import re
import textwrap
from pathlib import Path

import pytest

from scripts.workflow_quality_gate_validate_patterns import (
    _looks_like_agent,
    check_cross_references,
    check_portability,
    count_content_lines,
    is_valid_semver,
    parse_frontmatter,
    validate_agent,
    validate_file,
    validate_rule,
    validate_skill,
    validate_workflow_contracts,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _write_skill(tmp_path, name, frontmatter_extra="", body=""):
    """Create a minimal valid skill for testing."""
    skill_dir = tmp_path / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    default_body = textwrap.dedent("""\
        # Test Skill

        Test skill description for validation purposes.

        **Request:** $ARGUMENTS

        ---

        ## STEP 1: Analyze Input

        1. Read the input provided by the user
        2. Parse the data into structured format
        3. Validate format matches expected schema
        4. Identify any edge cases or special handling needed
        5. Document initial observations for later reference

        ## STEP 2: Execute Processing

        1. Apply the requested changes to target files
        2. Verify each change was applied correctly
        3. Report outcome of each modification
        4. Check for side effects or regressions
        5. Log all changes made for audit trail

        ## STEP 3: Verify Results

        1. Run validation checks on modified files
        2. Compare output against expected results
        3. Flag any discrepancies for review
        4. Run regression tests if available
        5. Check for unintended side effects

        ## STEP 4: Report Findings

        1. Summarize all findings in structured format
        2. Output results with file references
        3. Provide recommendations for follow-up
        4. Include severity ratings for each finding
        5. Suggest next steps for the user

        ## CRITICAL RULES

        - Always verify before reporting completion
        - Never skip validation steps even under time pressure
        - Report all findings including warnings and info
        - Escalate to user if confidence is low
        - Do not modify files outside the stated scope
        - Each iteration must try a different approach
        - Maximum 5 iterations before asking for help
    """)
    content = textwrap.dedent(f"""\
        ---
        name: {name}
        description: >
          Validate test patterns when running quality checks.
        allowed-tools: "Bash Read Grep Glob Write Edit"
        argument-hint: "<input>"
        type: workflow
        version: "1.0.0"
        {frontmatter_extra}
        ---

    """) + (body or default_body)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


def _write_agent(tmp_path, name, frontmatter_extra="", body=""):
    """Create a minimal valid agent for testing."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    default_body = textwrap.dedent("""\
        You are a test agent.

        ## Core Responsibilities

        1. Testing things

        ## Output Format

        ```
        Test report
        ```
    """)
    content = textwrap.dedent(f"""\
        ---
        name: {name}
        description: Test agent.
        model: inherit
        {frontmatter_extra}
        ---

    """) + (body or default_body)
    (agents_dir / f"{name}.md").write_text(content, encoding="utf-8")
    return agents_dir / f"{name}.md"


def _write_rule(tmp_path, name, content=None):
    """Create a minimal valid rule for testing."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    default_content = textwrap.dedent(f"""\
        ---
        description: Test rule.
        globs: ["**/*.py"]
        ---

        # Test Rule

        ## Section 1

        MUST do X when Y happens.
        Use Z instead of W.
        This prevents A from causing B.

        ## Section 2

        MUST NOT do P without Q.
        Always verify R before S.
        Check T against U.
        Validate V with W.
    """)
    (rules_dir / f"{name}.md").write_text(content or default_content, encoding="utf-8")
    return rules_dir / f"{name}.md"


# ── Unit Tests: parse_frontmatter ───────────────────────────────────────────


class TestParseFrontmatter:
    def test_valid_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: '1.0.0'\n---\n# Body", encoding="utf-8")
        fm = parse_frontmatter(f)
        assert fm["name"] == "test"
        assert fm["version"] == "1.0.0"

    def test_missing_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# No frontmatter here", encoding="utf-8")
        assert parse_frontmatter(f) is None

    def test_invalid_yaml(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\n: invalid: yaml: here\n---\n", encoding="utf-8")
        assert parse_frontmatter(f) is None


# ── Unit Tests: is_valid_semver ─────────────────────────────────────────────


class TestSemver:
    def test_valid_versions(self):
        assert is_valid_semver("1.0.0")
        assert is_valid_semver("2.3.14")
        assert is_valid_semver("0.0.1")

    def test_invalid_versions(self):
        assert not is_valid_semver("1.0")
        assert not is_valid_semver("v1.0.0")
        assert not is_valid_semver("1.0.0-beta")
        assert not is_valid_semver("latest")


# ── Skill Validation Tests ──────────────────────────────────────────────────


class TestValidateSkill:
    def test_valid_skill_passes(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "test-skill")
        errors = validate_skill(skill_dir)
        assert len(errors) == 0

    def test_missing_skill_md(self, tmp_path):
        skill_dir = tmp_path / "skills" / "empty-skill"
        skill_dir.mkdir(parents=True)
        errors = validate_skill(skill_dir)
        assert any("Missing SKILL.md" in e for e in errors)

    def test_missing_version(self, tmp_path):
        skill_dir = tmp_path / "skills" / "no-version"
        skill_dir.mkdir(parents=True)
        content = textwrap.dedent("""\
            ---
            name: no-version
            description: Test.
            allowed-tools: "Read"
            argument-hint: "<x>"
            type: workflow
            ---

            # Test

            Body content here with enough lines to not be a stub.

            ## STEP 1: Do thing

            1. First action
            2. Second action
            3. Third action

            ## STEP 2: Verify

            1. Check results
            2. Report findings
            3. Clean up

            ## CRITICAL RULES

            - Always verify
            - Never skip steps
            - Report all issues
        """)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        errors = validate_skill(skill_dir)
        assert any("Missing 'version'" in e for e in errors)

    def test_missing_type(self, tmp_path):
        skill_dir = tmp_path / "skills" / "no-type"
        skill_dir.mkdir(parents=True)
        content = textwrap.dedent("""\
            ---
            name: no-type
            description: Test.
            allowed-tools: "Read"
            argument-hint: "<x>"
            version: "1.0.0"
            ---

            # Test

            Body content here.

            ## STEP 1: Do thing

            1. Action one
            2. Action two
            3. Action three

            ## STEP 2: Verify

            1. Check one
            2. Check two
            3. Check three

            ## CRITICAL RULES

            - Rule one
            - Rule two
            - Rule three
        """)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        errors = validate_skill(skill_dir)
        assert any("Missing 'type'" in e for e in errors)

    def test_invalid_type(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "bad-type", frontmatter_extra='')
        # Rewrite with invalid type
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        content = content.replace("type: workflow", "type: action")
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        errors = validate_skill(skill_dir)
        assert any("Invalid type" in e for e in errors)

    def test_name_mismatch(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "actual-name")
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        content = content.replace("name: actual-name", "name: wrong-name")
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        errors = validate_skill(skill_dir)
        assert any("doesn't match directory" in e for e in errors)

    def test_workflow_without_steps(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "no-steps", body=textwrap.dedent("""\
            # No Steps Skill

            This skill has no step sections but claims to be a workflow.

            ## Section A

            Some content here that is not a step.
            More content to avoid stub detection.
            Even more content for padding.

            ## Section B

            Additional content for the skill.
            This makes it long enough to pass stub checks.
            And a bit more for good measure.

            ## Section C

            Final section with more content.
            Enough lines to not trigger stub.
            Last line of content here.

            ## Section D

            Extra content padding.
            More padding here.
            Even more padding.

            ## Section E

            Final padding section.
            Almost done.
            Done now.
        """))
        errors = validate_skill(skill_dir)
        assert any("no '## STEP N:' sections found" in e for e in errors)

    def test_placeholder_detected(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "has-todo", body=textwrap.dedent("""\
            # Test Skill

            <!-- TODO: fill this in -->

            ## STEP 1: Analyze

            1. Read the input
            2. Parse the data
            3. Validate format

            ## STEP 2: Execute

            1. Apply changes
            2. Verify results
            3. Report outcome

            ## STEP 3: Report

            1. Summarize findings
            2. Output results
            3. Clean up

            ## CRITICAL RULES

            - Always verify
            - Never skip
            - Report all
        """))
        errors = validate_skill(skill_dir)
        assert any("placeholder marker" in e for e in errors)

    def test_invalid_semver(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "bad-ver")
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        content = content.replace('version: "1.0.0"', 'version: "latest"')
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        errors = validate_skill(skill_dir)
        assert any("Invalid semver" in e for e in errors)


# ── Agent Validation Tests ──────────────────────────────────────────────────


class TestValidateAgent:
    def test_valid_agent_passes(self, tmp_path):
        agent_path = _write_agent(tmp_path, "test-agent")
        errors = validate_agent(agent_path)
        assert len(errors) == 0

    def test_missing_model(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)
        content = "---\nname: no-model\ndescription: Test.\n---\n\nBody"
        (agents_dir / "no-model.md").write_text(content, encoding="utf-8")
        errors = validate_agent(agents_dir / "no-model.md")
        assert any("Missing 'model'" in e for e in errors)

    def test_invalid_model(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)
        content = "---\nname: bad-model\ndescription: Test.\nmodel: gpt-4\n---\n\nBody"
        (agents_dir / "bad-model.md").write_text(content, encoding="utf-8")
        errors = validate_agent(agents_dir / "bad-model.md")
        assert any("Invalid model" in e for e in errors)


# ── Rule Validation Tests ───────────────────────────────────────────────────


class TestValidateRule:
    def test_valid_scoped_rule_passes(self, tmp_path):
        rule_path = _write_rule(tmp_path, "good-rule")
        errors = validate_rule(rule_path)
        assert len(errors) == 0

    def test_valid_global_rule_passes(self, tmp_path):
        rule_path = _write_rule(tmp_path, "global-rule", content=textwrap.dedent("""\
            ---
            description: A global rule.
            ---
            # Scope: global

            # Global Rule

            MUST do X in all contexts.
            Use Y instead of Z.
            This prevents A from causing B.
            Always check C before D.

            ## Details

            More details about the rule.
            Additional context here.
            Final notes on usage.
        """))
        errors = validate_rule(rule_path)
        assert len(errors) == 0

    def test_missing_scope(self, tmp_path):
        rule_path = _write_rule(tmp_path, "no-scope", content=textwrap.dedent("""\
            ---
            description: No scope defined.
            ---

            # Unscoped Rule

            MUST do X.
            Use Y instead of Z.
            This prevents A from causing B.
            Always check C before D.

            ## Details

            More details here.
            Additional notes.
            Final context.
        """))
        errors = validate_rule(rule_path)
        assert any("Missing scope" in e for e in errors)

    def test_placeholder_in_rule(self, tmp_path):
        rule_path = _write_rule(tmp_path, "stub-rule", content=textwrap.dedent("""\
            ---
            description: Stub rule.
            globs: ["**/*.py"]
            ---

            # Stub Rule

            ## Section 1
            <!-- TODO: fill this in -->

            Content here to pad lines.
            More content for padding.
            Even more content here.

            ## Section 2

            Additional content.
            More padding lines.
            Final lines here.
        """))
        errors = validate_rule(rule_path)
        assert any("placeholder marker" in e for e in errors)


# ── Portability Tests ───────────────────────────────────────────────────────


class TestPortability:
    def test_hardcoded_windows_path(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n---\n\nUse C:\\Users\\john\\project as the base.", encoding="utf-8")
        errors = check_portability(f)
        assert any("Hardcoded path" in e for e in errors)

    def test_hardcoded_linux_path(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n---\n\nFiles are in /home/deploy/app/.", encoding="utf-8")
        errors = check_portability(f)
        assert any("Hardcoded path" in e for e in errors)

    def test_paths_in_code_blocks_ok(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n---\n\n```\nC:\\Users\\example\\path\n```", encoding="utf-8")
        errors = check_portability(f)
        assert len(errors) == 0

    def test_clean_file_passes(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n---\n\nUse $PROJECT_ROOT/src as the base.", encoding="utf-8")
        errors = check_portability(f)
        assert len(errors) == 0


# ── Cross-Reference Tests ──────────────────────────────────────────────────


class TestCrossReferences:
    def test_valid_reference(self, tmp_path):
        _write_skill(tmp_path, "fix-loop")
        target = _write_skill(tmp_path, "caller", body=textwrap.dedent("""\
            # Caller Skill

            Delegates to fix-loop.

            ## STEP 1: Call fix-loop

            1. Skill("fix-loop", args="test")
            2. Wait for result
            3. Check outcome

            ## STEP 2: Report

            1. Summarize
            2. Output
            3. Clean up

            ## CRITICAL RULES

            - Always delegate
            - Never skip
            - Report all
        """))
        errors = check_cross_references(tmp_path / "skills")
        assert len(errors) == 0

    def test_dead_reference(self, tmp_path):
        _write_skill(tmp_path, "caller", body=textwrap.dedent("""\
            # Caller Skill

            Delegates to non-existent skill.

            ## STEP 1: Call missing skill

            1. Skill("nonexistent-skill", args="test")
            2. Wait for result
            3. Check outcome

            ## STEP 2: Report

            1. Summarize
            2. Output
            3. Clean up

            ## CRITICAL RULES

            - Always delegate
            - Never skip
            - Report all
        """))
        errors = check_cross_references(tmp_path / "skills")
        assert any("nonexistent-skill" in e for e in errors)


# ── Integration Test: validate actual patterns ──────────────────────────────


class TestActualPatterns:
    """Run the validator against the real core/.claude/ patterns."""

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "core" / ".claude").exists(),
        reason="core/.claude/ not found"
    )
    def test_all_skills_have_required_fields(self):
        """Every skill must have name, description, version, type in frontmatter."""
        skills_dir = Path(__file__).parent.parent.parent / "core" / ".claude" / "skills"
        missing = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            fm = parse_frontmatter(skill_md)
            if fm is None:
                missing.append(f"{skill_dir.name}: no frontmatter")
                continue
            for field in ("name", "description", "version", "type"):
                if field not in fm:
                    missing.append(f"{skill_dir.name}: missing {field}")
        assert len(missing) == 0, f"Skills with missing fields:\n" + "\n".join(missing)

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "core" / ".claude").exists(),
        reason="core/.claude/ not found"
    )
    def test_all_rules_have_scope(self):
        """Every rule must have globs: or # Scope: global."""
        rules_dir = Path(__file__).parent.parent.parent / "core" / ".claude" / "rules"
        missing = []
        for rule_path in sorted(rules_dir.glob("*.md")):
            if rule_path.name == "README.md":
                continue
            content = rule_path.read_text(encoding="utf-8")
            fm = parse_frontmatter(rule_path)
            has_globs = fm and ("globs" in fm or "paths" in fm)
            has_scope = "# Scope: global" in "\n".join(content.splitlines()[:10])
            if not has_globs and not has_scope:
                missing.append(rule_path.stem)
        assert len(missing) == 0, f"Rules without scope: {missing}"

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "core" / ".claude").exists(),
        reason="core/.claude/ not found"
    )
    def test_no_placeholder_rules(self):
        """No rules should contain TODO/FIXME placeholders (outside code blocks/inline code)."""
        rules_dir = Path(__file__).parent.parent.parent / "core" / ".claude" / "rules"
        placeholder_rules = []
        for rule_path in sorted(rules_dir.glob("*.md")):
            if rule_path.name == "README.md":
                continue
            content = rule_path.read_text(encoding="utf-8")
            # Strip code blocks and inline code before checking
            stripped = re.sub(r"```[\s\S]*?```", "", content)
            stripped = re.sub(r"`[^`]+`", "", stripped)
            for pattern in [r"<!--\s*TODO:", r"<!--\s*FIXME:", r"<!--\s*PLACEHOLDER"]:
                if re.search(pattern, stripped, re.IGNORECASE):
                    placeholder_rules.append(rule_path.stem)
                    break
        assert len(placeholder_rules) == 0, f"Rules with placeholders: {placeholder_rules}"


# ── Single-File Validation ─────────────────────────────────────────────────


class TestValidateFile:
    def test_validate_file_skill(self, tmp_path):
        skill_dir = _write_skill(tmp_path, "test-skill")
        errors = validate_file(skill_dir / "SKILL.md")
        assert errors == []

    def test_validate_file_rule(self, tmp_path):
        rule_path = _write_rule(tmp_path, "test-rule")
        errors = validate_file(rule_path)
        assert errors == []

    def test_validate_file_agent(self, tmp_path):
        agent_path = _write_agent(tmp_path, "test-agent")
        errors = validate_file(agent_path)
        assert errors == []

    def test_validate_file_nonexistent(self, tmp_path):
        errors = validate_file(tmp_path / "nonexistent.md")
        assert len(errors) == 1
        assert "File not found" in errors[0]

    def test_validate_file_invalid_skill(self, tmp_path):
        skill_dir = tmp_path / "skills" / "bad-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("no frontmatter here", encoding="utf-8")
        errors = validate_file(skill_dir / "SKILL.md")
        assert any("frontmatter" in e.lower() for e in errors)

    def test_looks_like_agent_true(self, tmp_path):
        agent_path = _write_agent(tmp_path, "my-agent")
        assert _looks_like_agent(agent_path) is True

    def test_looks_like_agent_false_for_rule(self, tmp_path):
        rule_path = _write_rule(tmp_path, "my-rule")
        assert _looks_like_agent(rule_path) is False


# ── Workflow Contracts Validation Tests ───────────────────────────────────


def _write_contracts(tmp_path, yaml_content):
    """Write a workflow-contracts.yaml file and return its path."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    contracts_path = config_dir / "workflow-contracts.yaml"
    contracts_path.write_text(yaml_content, encoding="utf-8")
    return contracts_path


def _setup_skill(tmp_path, name):
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = tmp_path / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\n---\n# {name}\nBody content.",
        encoding="utf-8",
    )
    return skill_dir


def _setup_agent(tmp_path, name):
    """Create a minimal agent .md file."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / f"{name}.md").write_text(
        f"---\nname: {name}\nmodel: inherit\n---\n# {name}\nBody.",
        encoding="utf-8",
    )
    return agents_dir / f"{name}.md"


class TestValidateWorkflowContracts:
    def test_missing_file_returns_empty(self, tmp_path):
        errors = validate_workflow_contracts(
            contracts_path=tmp_path / "nonexistent.yaml",
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert errors == []

    def test_invalid_yaml(self, tmp_path):
        path = _write_contracts(tmp_path, ": bad: yaml: [")
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("Failed to parse YAML" in e for e in errors)

    def test_missing_workflows_key(self, tmp_path):
        path = _write_contracts(tmp_path, "defaults:\n  max_retries: 3\n")
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("Missing 'workflows'" in e for e in errors)

    def test_valid_workflow_no_errors(self, tmp_path):
        _setup_skill(tmp_path, "brainstorm")
        _setup_skill(tmp_path, "writing-plans")
        _setup_agent(tmp_path, "dev-master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              dev:
                master_agent: dev-master-agent
                steps:
                  - id: ideate
                    skill: brainstorm
                    depends_on: []
                    artifacts_out:
                      spec: { path: "docs/spec.md" }
                  - id: plan
                    skill: writing-plans
                    depends_on: [ideate]
                    artifacts_in:
                      spec: "ideate.artifacts_out.spec"
                    artifacts_out:
                      plan: { path: "docs/plan.md" }
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert errors == []

    def test_missing_skill_reference(self, tmp_path):
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              test-wf:
                master_agent: master-agent
                steps:
                  - id: do_thing
                    skill: nonexistent-skill
                    depends_on: []
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("nonexistent-skill" in e and "does not exist" in e for e in errors)

    def test_missing_dispatch_agent(self, tmp_path):
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              test-wf:
                master_agent: master-agent
                steps:
                  - id: exec
                    dispatch: ghost-agent
                    depends_on: []
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("ghost-agent" in e and "does not exist" in e for e in errors)

    def test_missing_master_agent(self, tmp_path):
        _setup_skill(tmp_path, "my-skill")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              test-wf:
                master_agent: missing-master-agent
                steps:
                  - id: step1
                    skill: my-skill
                    depends_on: []
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("missing-master-agent" in e and "does not exist" in e for e in errors)

    def test_missing_sub_orchestrator_agent(self, tmp_path):
        _setup_skill(tmp_path, "my-skill")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              test-wf:
                master_agent: master-agent
                sub_orchestrators:
                  - agent: phantom-agent
                    role: "Does not exist"
                steps:
                  - id: step1
                    skill: my-skill
                    depends_on: []
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("phantom-agent" in e and "does not exist" in e for e in errors)

    def test_dag_cycle_detected(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_skill(tmp_path, "skill-b")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              cycle-wf:
                master_agent: master-agent
                steps:
                  - id: a
                    skill: skill-a
                    depends_on: [b]
                  - id: b
                    skill: skill-b
                    depends_on: [a]
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("DAG cycle" in e for e in errors)

    def test_dag_self_cycle(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              self-cycle-wf:
                master_agent: master-agent
                steps:
                  - id: a
                    skill: skill-a
                    depends_on: [a]
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("DAG cycle" in e for e in errors)

    def test_depends_on_unknown_step(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              bad-dep-wf:
                master_agent: master-agent
                steps:
                  - id: a
                    skill: skill-a
                    depends_on: [nonexistent_step]
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("unknown step 'nonexistent_step'" in e for e in errors)

    def test_artifact_in_valid_reference(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_skill(tmp_path, "skill-b")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              art-wf:
                master_agent: master-agent
                steps:
                  - id: produce
                    skill: skill-a
                    depends_on: []
                    artifacts_out:
                      data: { path: "out/data.json" }
                  - id: consume
                    skill: skill-b
                    depends_on: [produce]
                    artifacts_in:
                      data: "produce.artifacts_out.data"
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert errors == []

    def test_artifact_in_references_unknown_step(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              bad-art-wf:
                master_agent: master-agent
                steps:
                  - id: consume
                    skill: skill-a
                    depends_on: []
                    artifacts_in:
                      data: "ghost_step.artifacts_out.data"
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("unknown step 'ghost_step'" in e for e in errors)

    def test_artifact_in_references_nonexistent_artifact_out(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_skill(tmp_path, "skill-b")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              bad-art-key-wf:
                master_agent: master-agent
                steps:
                  - id: produce
                    skill: skill-a
                    depends_on: []
                    artifacts_out:
                      actual_key: { path: "out/data.json" }
                  - id: consume
                    skill: skill-b
                    depends_on: [produce]
                    artifacts_in:
                      data: "produce.artifacts_out.wrong_key"
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("non-existent artifact_out 'wrong_key'" in e for e in errors)

    def test_artifact_in_invalid_format(self, tmp_path):
        _setup_skill(tmp_path, "skill-a")
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              bad-fmt-wf:
                master_agent: master-agent
                steps:
                  - id: consume
                    skill: skill-a
                    depends_on: []
                    artifacts_in:
                      data: "just_a_string"
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("invalid reference format" in e for e in errors)

    def test_no_steps_defined(self, tmp_path):
        _setup_agent(tmp_path, "master-agent")
        path = _write_contracts(tmp_path, textwrap.dedent("""\
            workflows:
              empty-wf:
                master_agent: master-agent
                steps: []
        """))
        errors = validate_workflow_contracts(
            contracts_path=path,
            skills_dir=tmp_path / "skills",
            agents_dir=tmp_path / "agents",
        )
        assert any("No steps defined" in e for e in errors)

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "config" / "workflow-contracts.yaml").exists(),
        reason="config/workflow-contracts.yaml not found",
    )
    def test_real_workflow_contracts_valid(self):
        """The actual workflow-contracts.yaml should pass validation."""
        root = Path(__file__).parent.parent.parent
        errors = validate_workflow_contracts(
            contracts_path=root / "config" / "workflow-contracts.yaml",
            skills_dir=root / "core" / ".claude" / "skills",
            agents_dir=root / "core" / ".claude" / "agents",
        )
        assert errors == [], f"Workflow contracts errors:\n" + "\n".join(errors)
