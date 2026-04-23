"""Tests for assign_workflow_groups.py"""

import pytest

from scripts.assign_workflow_groups import (
    NEEDS_REVIEW_GROUP,
    compute_assignments,
    find_orphans,
    score_keywords,
    score_reference_graph,
)


def _make_definitions():
    return {
        "testing-pipeline": {
            "description": "Test execution, verification, quality enforcement.",
            "seeds": {
                "skills": ["auto-verify", "fix-loop"],
                "agents": ["tester-agent"],
                "rules": ["testing"],
            },
        },
        "documentation": {
            "description": "Documentation generation and maintenance.",
            "seeds": {
                "skills": ["adr", "diataxis-docs"],
                "agents": [],
                "rules": [],
            },
        },
    }


def _make_graph(nodes_data):
    nodes = {}
    for name, ptype, refs_out, refs_in, desc in nodes_data:
        nodes[name] = {
            "type": ptype,
            "refs_out": refs_out,
            "refs_in": refs_in,
            "description": desc,
            "path": f"core/.claude/skills/{name}/SKILL.md",
        }
    return {"nodes": nodes, "edges": []}


class TestFindOrphans:
    def test_identifies_unseeded_patterns(self):
        definitions = _make_definitions()
        all_patterns = {
            "auto-verify", "fix-loop", "tester-agent",
            "testing", "adr", "diataxis-docs", "new-skill",
        }
        orphans = find_orphans(definitions, all_patterns)
        assert orphans == {"new-skill"}

    def test_no_orphans_when_all_seeded(self):
        definitions = _make_definitions()
        all_patterns = {
            "auto-verify", "fix-loop", "tester-agent",
            "testing", "adr", "diataxis-docs",
        }
        orphans = find_orphans(definitions, all_patterns)
        assert orphans == set()

    def test_multiple_orphans(self):
        definitions = _make_definitions()
        all_patterns = {
            "auto-verify", "fix-loop", "tester-agent",
            "testing", "adr", "diataxis-docs",
            "skill-a", "skill-b",
        }
        orphans = find_orphans(definitions, all_patterns)
        assert orphans == {"skill-a", "skill-b"}


class TestScoreReferenceGraph:
    def test_scores_based_on_shared_refs(self):
        graph = _make_graph([
            ("new-skill", "skill", ["auto-verify", "fix-loop"], [], ""),
            ("auto-verify", "skill", [], ["new-skill"], ""),
            ("fix-loop", "skill", [], ["new-skill"], ""),
        ])
        group_seeds = {"auto-verify", "fix-loop", "tester-agent", "testing"}
        score = score_reference_graph("new-skill", group_seeds, graph)
        assert score == 6  # 2 matches * 3

    def test_zero_when_no_overlap(self):
        graph = _make_graph([
            ("new-skill", "skill", ["unrelated"], [], ""),
        ])
        score = score_reference_graph("new-skill", {"auto-verify"}, graph)
        assert score == 0

    def test_counts_incoming_refs_too(self):
        graph = _make_graph([
            ("new-skill", "skill", [], ["auto-verify"], ""),
            ("auto-verify", "skill", ["new-skill"], [], ""),
        ])
        score = score_reference_graph("new-skill", {"auto-verify"}, graph)
        assert score == 3  # 1 match * 3

    def test_missing_node_returns_zero(self):
        graph = _make_graph([])
        score = score_reference_graph("nonexistent", {"auto-verify"}, graph)
        assert score == 0


class TestScoreKeywords:
    def test_matches_group_name_words(self):
        score = score_keywords(
            "jest-dev", "Configure and run Jest testing",
            "testing-pipeline", "Testing execution and verification",
            {"auto-verify", "fix-loop"},
        )
        assert score >= 1  # "testing" matches

    def test_zero_for_unrelated(self):
        score = score_keywords(
            "redis-patterns", "Apply Redis caching patterns",
            "documentation", "Documentation generation",
            {"adr", "diataxis-docs"},
        )
        assert score == 0

    def test_matches_seed_name_tokens(self):
        score = score_keywords(
            "doc-staleness", "Detect stale documentation",
            "documentation", "Documentation generation",
            {"adr", "diataxis-docs"},
        )
        # "doc" from seed "diataxis-docs" + "documentation" from group desc
        assert score >= 1


class TestComputeAssignments:
    def test_high_confidence_assignment(self):
        definitions = _make_definitions()
        graph = _make_graph([
            ("new-test-skill", "skill", ["auto-verify", "fix-loop"], [], "Run test verification"),
            ("auto-verify", "skill", [], ["new-test-skill"], ""),
            ("fix-loop", "skill", [], ["new-test-skill"], ""),
            ("tester-agent", "agent", [], [], ""),
            ("testing", "rule", [], [], ""),
            ("adr", "skill", [], [], ""),
            ("diataxis-docs", "skill", [], [], ""),
        ])
        assignments = compute_assignments({"new-test-skill"}, definitions, graph)
        testing_entries = assignments["testing-pipeline"]
        assert any(e[0] == "new-test-skill" for e in testing_entries)
        # High confidence: score should be >= 4
        entry = next(e for e in testing_entries if e[0] == "new-test-skill")
        assert entry[2] >= 4

    def test_no_refs_goes_to_needs_review(self):
        definitions = _make_definitions()
        graph = _make_graph([
            ("mystery-skill", "skill", [], [], "Something completely unrelated xyzzy"),
            ("auto-verify", "skill", [], [], ""),
            ("fix-loop", "skill", [], [], ""),
            ("tester-agent", "agent", [], [], ""),
            ("testing", "rule", [], [], ""),
            ("adr", "skill", [], [], ""),
            ("diataxis-docs", "skill", [], [], ""),
        ])
        assignments = compute_assignments({"mystery-skill"}, definitions, graph)
        review_entries = assignments[NEEDS_REVIEW_GROUP]
        assert any(e[0] == "mystery-skill" for e in review_entries)

    def test_low_confidence_with_refs_goes_to_single_best_group(self):
        """Score 2-3 with at least one ref-graph match → single best group."""
        definitions = _make_definitions()
        graph = _make_graph([
            # Has a ref to auto-verify (ref_score=3) + keyword "test" (kw_score=0) = 3
            ("some-test-helper", "skill", ["auto-verify"], [], "Helper utility"),
            ("auto-verify", "skill", [], ["some-test-helper"], ""),
            ("fix-loop", "skill", [], [], ""),
            ("tester-agent", "agent", [], [], ""),
            ("testing", "rule", [], [], ""),
            ("adr", "skill", [], [], ""),
            ("diataxis-docs", "skill", [], [], ""),
        ])
        assignments = compute_assignments({"some-test-helper"}, definitions, graph)
        groups_with_entry = [
            wf for wf, entries in assignments.items()
            if wf != NEEDS_REVIEW_GROUP and any(e[0] == "some-test-helper" for e in entries)
        ]
        assert len(groups_with_entry) == 1
        assert groups_with_entry[0] == "testing-pipeline"

    def test_empty_orphans_returns_empty(self):
        definitions = _make_definitions()
        graph = _make_graph([])
        assignments = compute_assignments(set(), definitions, graph)
        total = sum(len(entries) for entries in assignments.values())
        assert total == 0

    def test_score_1_keyword_only_goes_to_needs_review(self):
        """Score 1 from keyword match alone is too weak — should go to
        _needs-manual-review, not a real workflow group."""
        definitions = {
            "development-loop": {
                "description": "The core build cycle: ideate, plan, implement, verify, commit.",
                "seeds": {
                    "skills": ["brainstorm", "implement", "writing-plans"],
                    "agents": [],
                    "rules": ["workflow"],
                },
            },
        }
        graph = _make_graph([
            # "tailwind-dev" has no refs, will score 1 on keyword "dev"
            # matching "development" in the group name
            ("tailwind-dev", "skill", [], [], "Apply Tailwind CSS patterns"),
            ("brainstorm", "skill", [], [], ""),
            ("implement", "skill", [], [], ""),
            ("writing-plans", "skill", [], [], ""),
        ])
        # Manually add the rule node
        graph["nodes"]["workflow"] = {
            "type": "rule", "refs_out": [], "refs_in": [],
            "description": "", "path": "core/.claude/rules/workflow.md",
        }
        assignments = compute_assignments({"tailwind-dev"}, definitions, graph)
        # Score 1 keyword-only should go to needs-review, not development-loop
        review_entries = [e[0] for e in assignments.get(NEEDS_REVIEW_GROUP, [])]
        dev_entries = [e[0] for e in assignments.get("development-loop", [])]
        assert "tailwind-dev" in review_entries, \
            f"tailwind-dev should be in needs-review but was in development-loop: {dev_entries}"


class TestWorkflowGroupBalance:
    """Tests for workflow group size balance in current config."""

    def test_no_group_exceeds_max_seeds(self):
        """No single workflow group should have >80 seeds in the config.
        Testing-pipeline is naturally the largest (many test frameworks + agents +
        the three-lane spec added 6 new patterns: failure-triage-agent,
        github-issue-manager-agent, agent-evaluator, create-github-issue,
        serialize-fixes, escalation-report)."""
        from scripts.generate_workflow_docs import load_workflow_definitions

        definitions = load_workflow_definitions()

        for wf_name, wf_def in definitions.items():
            seeds = wf_def.get("seeds", {})
            total = sum(len(seeds.get(cat, [])) for cat in ("skills", "agents", "rules"))
            assert total <= 80, \
                f"{wf_name} has {total} seeds (max 80)"
