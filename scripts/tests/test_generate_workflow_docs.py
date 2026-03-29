"""Tests for generate_workflow_docs.py Mermaid generation.

Covers the five root-cause bugs:
1. Backticks in step titles break Mermaid labels
2. Duplicate step numbers produce conflicting node definitions
3. Dangling _ext references to nonexistent skills/agents
4. Self-loop edges from duplicate steps
5. Oversized graphs (too many skills) should be capped
"""

import pytest

from scripts.generate_workflow_docs import (
    extract_steps,
    generate_detailed_mermaid,
    generate_mermaid_flow,
)


# ── extract_steps tests ──────────────────────────────────────────


class TestExtractSteps:
    def test_basic_step_extraction(self):
        body = """
## STEP 1: Do Something
Some content here.

## STEP 2: Do Another Thing
More content.

## STEP 3: Finish Up
Final content.
"""
        steps = extract_steps("test-skill", body)
        assert len(steps) == 3
        assert steps[0]["num"] == "1"
        assert steps[0]["title"] == "Do Something"
        assert steps[2]["title"] == "Finish Up"

    def test_duplicate_step_numbers_deduplicated(self):
        """Bug: some skills have irregular formatting that produces
        duplicate step numbers. Only the first match should be kept."""
        body = """
## STEP 1: Real Title
Real content with details.

## STEP 2: Another Real Title
More real content.

## STEP 2: [Verb Phrase]
This is a template placeholder that should be ignored.

## STEP 3: Final Step
End content.
"""
        steps = extract_steps("test-skill", body)
        nums = [s["num"] for s in steps]
        # No duplicate step numbers
        assert len(nums) == len(set(nums)), f"Duplicate step numbers: {nums}"
        # Step 2 should have the first (real) title, not the placeholder
        step2 = next(s for s in steps if s["num"] == "2")
        assert "[Verb Phrase]" not in step2["title"]

    def test_backticks_stripped_from_titles(self):
        """Bug: backticks in step titles break Mermaid double-quoted labels."""
        body = """
## STEP 1: Configure Something
Content.

## STEP 2: Write Tests Using `bun:test` Patterns
Content about bun test.

## STEP 3: Mock Dependencies with `bun:test` Spy
More content.
"""
        steps = extract_steps("test-skill", body)
        for step in steps:
            assert "`" not in step["title"], \
                f"Step {step['num']} title contains backtick: {step['title']}"

    def test_example_skill_refs_filtered(self):
        """Bug: generic example text like `/skill-name` or `/clear`
        should not appear as skill_calls."""
        body = """
## STEP 1: Do Setup
Use `/fix-loop` to fix issues.

## STEP 2: Example Section
See `/skill-name` for the pattern.
Also `/clear` the cache.

## STEP 3: Real Delegation
Delegate to `/auto-verify`.
"""
        steps = extract_steps("test-skill", body)
        all_calls = set()
        for step in steps:
            all_calls.update(step["skill_calls"])
        # Real skills should be present
        assert "fix-loop" in all_calls
        assert "auto-verify" in all_calls
        # Generic placeholders should be filtered
        assert "skill-name" not in all_calls
        assert "clear" not in all_calls


# ── generate_detailed_mermaid tests ──────────────────────────────


def _make_workflow(skill_names, edges=None):
    """Helper to build a minimal workflow dict."""
    return {
        "skills": skill_names,
        "agents": [],
        "rules": [],
        "edges": edges or [],
    }


def _make_graph(skills_data):
    """Helper to build a minimal graph with steps.

    skills_data: list of (name, steps_list) tuples where steps_list
    contains dicts with at minimum 'num', 'title'.
    """
    nodes = {}
    for name, steps in skills_data:
        full_steps = []
        for s in steps:
            full_steps.append({
                "num": s.get("num", "1"),
                "title": s.get("title", "Step"),
                "skill_calls": s.get("skill_calls", []),
                "agent_calls": s.get("agent_calls", []),
                "has_gate": s.get("has_gate", False),
                "has_decision": False,
                "artifacts": s.get("artifacts", []),
                "artifacts_consumed": s.get("artifacts_consumed", []),
                "branches": s.get("branches", []),
            })
        nodes[name] = {
            "type": "skill",
            "path": f"core/.claude/skills/{name}/SKILL.md",
            "description": "",
            "version": "1.0.0",
            "label": "core",
            "refs_out": [],
            "refs_in": [],
            "steps": full_steps,
        }
    return {"nodes": nodes, "edges": []}


class TestGenerateDetailedMermaid:
    def test_no_duplicate_node_ids(self):
        """Bug: duplicate step nums produce conflicting node defs."""
        steps = [
            {"num": "1", "title": "First Step"},
            {"num": "2", "title": "Second Step"},
            {"num": "3", "title": "Third Step"},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = generate_detailed_mermaid(workflow, graph)

        # Count node definitions — each step_id should appear exactly once
        # as a node definition (not counting edge references)
        lines = result.split("\n")
        node_defs = {}
        for line in lines:
            stripped = line.strip()
            # Node definition: starts with ID followed by [ or {
            for step_id in ["my_skill_s1", "my_skill_s2", "my_skill_s3"]:
                if stripped.startswith(step_id + "[") or stripped.startswith(step_id + "{"):
                    node_defs.setdefault(step_id, []).append(stripped)

        for step_id, defs in node_defs.items():
            assert len(defs) == 1, \
                f"Node {step_id} defined {len(defs)} times: {defs}"

    def test_no_backticks_in_mermaid_labels(self):
        """Bug: backticks in labels break Mermaid rendering."""
        steps = [
            {"num": "1", "title": "Setup Config"},
            {"num": "2", "title": "Use bun:test Patterns"},
            {"num": "3", "title": "Run Tests"},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = generate_detailed_mermaid(workflow, graph)

        # No backticks inside mermaid node labels
        for line in result.split("\n"):
            if '["' in line:
                label = line.split('["')[1].split('"]')[0] if '"]' in line else ""
                assert "`" not in label, f"Backtick in label: {line.strip()}"

    def test_no_self_loop_edges(self):
        """Bug: self-loops appear when duplicate steps generate same node ID."""
        steps = [
            {"num": "1", "title": "First"},
            {"num": "2", "title": "Second"},
            {"num": "3", "title": "Third"},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = generate_detailed_mermaid(workflow, graph)

        for line in result.split("\n"):
            stripped = line.strip()
            if "-->" in stripped and "-.-->" not in stripped:
                parts = stripped.split("-->")
                src = parts[0].strip()
                tgt = parts[-1].strip()
                assert src != tgt, f"Self-loop edge: {stripped}"

    def test_ext_refs_only_for_existing_skills(self):
        """Bug: dangling _ext nodes for nonexistent skills like /skill-name."""
        steps = [
            {"num": "1", "title": "Setup"},
            {"num": "2", "title": "Delegate", "skill_calls": ["fix-loop", "skill-name"]},
            {"num": "3", "title": "Finish"},
        ]
        graph = _make_graph([
            ("my-skill", steps),
            ("fix-loop", [
                {"num": "1", "title": "A"},
                {"num": "2", "title": "B"},
                {"num": "3", "title": "C"},
            ]),
        ])
        workflow = _make_workflow(["my-skill"])
        result = generate_detailed_mermaid(workflow, graph)

        # fix-loop exists in graph, so its _ext node should be present
        assert "fix_loop_ext" in result
        # skill-name does NOT exist in graph, so its _ext should be absent
        assert "skill_name_ext" not in result

    def test_large_workflow_capped(self):
        """Graphs with >25 skills should return empty (use overview only)."""
        skill_names = [f"skill-{i}" for i in range(30)]
        skills_data = [
            (name, [
                {"num": "1", "title": "A"},
                {"num": "2", "title": "B"},
                {"num": "3", "title": "C"},
            ])
            for name in skill_names
        ]
        graph = _make_graph(skills_data)
        workflow = _make_workflow(skill_names)
        result = generate_detailed_mermaid(workflow, graph)

        assert result == "", \
            "Detailed mermaid should be empty for workflows with >25 skills"


# ── generate_mermaid_flow (overview) tests ───────────────────────


class TestGenerateMermaidFlow:
    def test_isolated_nodes_excluded(self):
        """Nodes with no edges should not appear in the overview graph."""
        workflow = {
            "skills": ["connected-a", "connected-b", "isolated-c"],
            "agents": [],
            "rules": [],
            "edges": [
                {"from": "connected-a", "to": "connected-b", "type": "Skill()"},
            ],
        }
        result = generate_mermaid_flow(workflow)
        assert "connected_a" in result
        assert "connected_b" in result
        assert "isolated_c" not in result
