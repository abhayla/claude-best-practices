"""Tests for generate_workflow_docs.py Mermaid generation, SVG rendering, and workflow steps.

Covers:
1. Backticks in step titles break Mermaid labels
2. Duplicate step numbers produce conflicting node definitions
3. Dangling _ext references to nonexistent skills/agents
4. Self-loop edges from duplicate steps
5. Oversized graphs (too many skills) should be capped
6. SVG image rendering via mmdc
7. --require-svg strict mode for CI enforcement
8. render_workflow_steps textual step detail rendering
"""

import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

from scripts.generate_workflow_docs import (
    extract_steps,
    generate_detailed_mermaid,
    generate_mermaid_flow,
    generate_per_skill_mermaid,
    generate_consolidated_step_flow,
    generate_entry_point_map,
    render_workflow_steps,
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


# ── SVG rendering tests ──────────────────────────────────────────


HAS_MMDC = shutil.which("mmdc") is not None


class TestRenderMermaidToSvg:
    """Tests for rendering Mermaid blocks to SVG images (mocked mmdc)."""

    def _mock_mmdc_run(self, output_path):
        """Create a mock subprocess.run that writes fake SVG to output_path."""
        def _run(cmd, **kwargs):
            # cmd is [mmdc_path, "-i", input, "-o", output, "-b", "transparent"]
            out = Path(cmd[4])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("<svg>mocked</svg>", encoding="utf-8")
            from subprocess import CompletedProcess
            return CompletedProcess(cmd, 0)
        return _run

    @patch("scripts.generate_workflow_docs.shutil.which", return_value="/usr/bin/mmdc")
    def test_render_simple_mermaid_to_svg(self, mock_which, tmp_path):
        from scripts.generate_workflow_docs import render_mermaid_to_svg

        mermaid_code = "graph LR\n    A --> B\n    B --> C"
        svg_path = tmp_path / "test.svg"
        with patch("scripts.generate_workflow_docs.subprocess.run",
                   side_effect=self._mock_mmdc_run(svg_path)):
            result = render_mermaid_to_svg(mermaid_code, svg_path)
        assert result is True
        assert svg_path.exists()
        content = svg_path.read_text(encoding="utf-8")
        assert "<svg" in content

    @patch("scripts.generate_workflow_docs.shutil.which", return_value="/usr/bin/mmdc")
    def test_render_invalid_mermaid_returns_false(self, mock_which, tmp_path):
        from scripts.generate_workflow_docs import render_mermaid_to_svg
        from subprocess import CompletedProcess

        mermaid_code = "this is not valid mermaid syntax {{{{{"
        svg_path = tmp_path / "bad.svg"
        with patch("scripts.generate_workflow_docs.subprocess.run",
                   return_value=CompletedProcess([], 1)):
            result = render_mermaid_to_svg(mermaid_code, svg_path)
        assert result is False

    @patch("scripts.generate_workflow_docs.shutil.which", return_value="/usr/bin/mmdc")
    def test_workflow_doc_contains_svg_image_link(self, mock_which, tmp_path):
        """After rendering, the markdown should contain ![](images/...) links."""
        from scripts.generate_workflow_docs import render_workflow_doc, embed_svg_images

        workflow = {
            "description": "Test workflow for SVG rendering.",
            "skills": ["skill-a", "skill-b"],
            "agents": [],
            "rules": [],
            "edges": [{"from": "skill-a", "to": "skill-b", "type": "Skill()"}],
        }
        graph = _make_graph([
            ("skill-a", [
                {"num": "1", "title": "Do A"},
                {"num": "2", "title": "Do B"},
                {"num": "3", "title": "Do C"},
            ]),
            ("skill-b", [
                {"num": "1", "title": "Do X"},
                {"num": "2", "title": "Do Y"},
                {"num": "3", "title": "Do Z"},
            ]),
        ])
        md_content = render_workflow_doc("test-workflow", workflow, graph)

        images_dir = tmp_path / "images"
        with patch("scripts.generate_workflow_docs.subprocess.run",
                   side_effect=self._mock_mmdc_run(images_dir)):
            result = embed_svg_images(md_content, "test-workflow", images_dir)

        assert "![" in result
        assert "images/" in result
        svg_files = list(images_dir.glob("*.svg"))
        assert len(svg_files) >= 1


# ── --require-svg strict mode tests ─────────────────────────────


class TestRequireSvgFlag:
    """Tests for --require-svg CLI flag that enforces SVG rendering in CI."""

    @patch("scripts.generate_workflow_docs.shutil.which", return_value=None)
    def test_require_svg_exits_when_mmdc_missing(self, mock_which):
        """--require-svg must exit 1 when mmdc is not installed."""
        from scripts.generate_workflow_docs import check_svg_requirements
        with pytest.raises(SystemExit) as exc_info:
            check_svg_requirements(require_svg=True)
        assert exc_info.value.code == 1

    @patch("scripts.generate_workflow_docs.shutil.which", return_value="/usr/bin/mmdc")
    def test_require_svg_passes_when_mmdc_available(self, mock_which):
        """--require-svg must not fail when mmdc is found."""
        from scripts.generate_workflow_docs import check_svg_requirements
        # Should not raise
        check_svg_requirements(require_svg=True)

    @patch("scripts.generate_workflow_docs.shutil.which", return_value=None)
    def test_no_require_svg_silently_degrades(self, mock_which):
        """Without --require-svg, missing mmdc should not cause failure."""
        from scripts.generate_workflow_docs import check_svg_requirements
        # Should not raise even though mmdc is missing
        check_svg_requirements(require_svg=False)

    @patch("scripts.generate_workflow_docs.shutil.which", return_value=None)
    def test_embed_svg_returns_unchanged_when_mmdc_missing(self, mock_which):
        """embed_svg_images must return content unchanged when mmdc missing."""
        from scripts.generate_workflow_docs import embed_svg_images
        md = "```mermaid\ngraph LR\n    A --> B\n```\n"
        result = embed_svg_images(md, "test", Path("/tmp/fake-images"))
        assert result == md
        assert "![" not in result

    def test_validate_svg_output_detects_missing_svgs(self, tmp_path):
        """validate_svg_output must fail when expected SVGs are missing."""
        from scripts.generate_workflow_docs import validate_svg_output
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        # No SVG files exist but workflow has mermaid blocks
        with pytest.raises(SystemExit) as exc_info:
            validate_svg_output("test-workflow", images_dir, expected_count=2)
        assert exc_info.value.code == 1

    def test_validate_svg_output_passes_when_svgs_exist(self, tmp_path):
        """validate_svg_output must pass when expected SVGs are present."""
        from scripts.generate_workflow_docs import validate_svg_output
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        # Create fake SVG files
        (images_dir / "test-workflow-1.svg").write_text("<svg></svg>")
        (images_dir / "test-workflow-2.svg").write_text("<svg></svg>")
        # Should not raise
        validate_svg_output("test-workflow", images_dir, expected_count=2)


# ── render_workflow_steps tests ────────────────────────────────────


class TestRenderWorkflowSteps:
    """Tests for the textual workflow steps section rendering."""

    def test_basic_step_rendering(self):
        """Skills with steps should produce a Workflow Steps section with tables."""
        steps = [
            {"num": "1", "title": "Analyze Requirements"},
            {"num": "2", "title": "Write Tests"},
            {"num": "3", "title": "Implement Code"},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = render_workflow_steps(workflow, graph)

        assert "## Workflow Steps" in result
        assert "### my-skill" in result
        assert "| Step | Title | Delegates To | Artifacts | Gates/Decisions |" in result
        assert "Analyze Requirements" in result
        assert "Write Tests" in result
        assert "Implement Code" in result

    def test_skills_without_steps_are_skipped(self):
        """Skills with no extracted steps should not appear in the section."""
        graph = _make_graph([
            ("has-steps", [
                {"num": "1", "title": "Do A"},
                {"num": "2", "title": "Do B"},
            ]),
            ("no-steps", []),
        ])
        workflow = _make_workflow(["has-steps", "no-steps"])
        result = render_workflow_steps(workflow, graph)

        assert "### has-steps" in result
        assert "### no-steps" not in result

    def test_empty_section_when_no_skills_have_steps(self):
        """If no skills have steps, return empty string (no section header)."""
        graph = _make_graph([("empty-skill", [])])
        workflow = _make_workflow(["empty-skill"])
        result = render_workflow_steps(workflow, graph)

        assert result == ""

    def test_delegations_rendered(self):
        """Skill and agent calls should appear in the Delegates To column."""
        steps = [
            {
                "num": "1", "title": "Setup",
                "skill_calls": ["fix-loop", "auto-verify"],
                "agent_calls": ["tester-agent"],
            },
            {"num": "2", "title": "Finish"},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = render_workflow_steps(workflow, graph)

        assert "`/fix-loop`" in result
        assert "`/auto-verify`" in result
        assert "`tester-agent`" in result

    def test_gate_indicator_rendered(self):
        """Steps with gates should show a gate indicator."""
        steps = [
            {"num": "1", "title": "Check Gate", "has_gate": True},
            {"num": "2", "title": "No Gate", "has_gate": False},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = render_workflow_steps(workflow, graph)

        # Match only table rows (start with |)
        lines = result.split("\n")
        gate_line = [l for l in lines if l.startswith("|") and "Check Gate" in l][0]
        no_gate_line = [l for l in lines if l.startswith("|") and "No Gate" in l][0]
        assert "gate" in gate_line.lower()
        # No Gate line should not have gate indicator in last column
        last_col = no_gate_line.rsplit("|", 2)[-2].strip()
        assert "gate" not in last_col.lower()

    def test_artifacts_rendered(self):
        """Produced and consumed artifacts should appear in the Artifacts column."""
        steps = [
            {
                "num": "1", "title": "Produce",
                "artifacts": ["test-results/unit.json"],
                "artifacts_consumed": [],
            },
            {
                "num": "2", "title": "Consume",
                "artifacts": [],
                "artifacts_consumed": ["test-results/unit.json"],
            },
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = render_workflow_steps(workflow, graph)

        # Match only table rows (start with |)
        lines = result.split("\n")
        produce_line = [l for l in lines if l.startswith("|") and "Produce" in l][0]
        consume_line = [l for l in lines if l.startswith("|") and "Consume" in l][0]
        assert "test-results/unit.json" in produce_line
        assert "test-results/unit.json" in consume_line

    def test_pipe_in_title_escaped(self):
        """Pipe characters in step titles must be escaped for markdown tables."""
        steps = [
            {"num": "1", "title": "Check A | B condition"},
            {"num": "2", "title": "Normal Title"},
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = render_workflow_steps(workflow, graph)

        # The raw pipe should be escaped
        assert "A \\| B" in result
        # Table structure should remain intact (no broken columns)
        # Count unescaped pipes only (exclude \|) — should be 6 for 5 columns
        for line in result.split("\n"):
            if line.startswith("|") and "Check A" in line:
                import re
                unescaped_pipes = len(re.findall(r'(?<!\\)\|', line))
                assert unescaped_pipes == 6, f"Broken table row: {line}"

    def test_branches_rendered(self):
        """Decision branches should appear in the Gates/Decisions column."""
        steps = [
            {
                "num": "1", "title": "Decision Point",
                "has_gate": True,
                "has_decision": True,
                "branches": [{"label": "PASS"}, {"label": "BLOCK"}],
            },
        ]
        graph = _make_graph([("my-skill", steps)])
        workflow = _make_workflow(["my-skill"])
        result = render_workflow_steps(workflow, graph)

        # Match only table rows (start with |)
        lines = result.split("\n")
        decision_line = [l for l in lines if l.startswith("|") and "Decision Point" in l][0]
        assert "PASS" in decision_line or "BLOCK" in decision_line

    def test_multiple_skills_each_get_subsection(self):
        """Each skill with steps gets its own sub-heading and table."""
        graph = _make_graph([
            ("skill-a", [{"num": "1", "title": "A1"}, {"num": "2", "title": "A2"}]),
            ("skill-b", [{"num": "1", "title": "B1"}, {"num": "2", "title": "B2"}]),
        ])
        workflow = _make_workflow(["skill-a", "skill-b"])
        result = render_workflow_steps(workflow, graph)

        assert "### skill-a" in result
        assert "### skill-b" in result
        # Each should have its own table header
        assert result.count("| Step | Title |") == 2


# ── generate_per_skill_mermaid tests ──────────────────────────────


class TestGeneratePerSkillMermaid:
    """Tests for per-skill step flowcharts within the Workflow Steps section."""

    def test_basic_step_flow(self):
        """Should produce a mermaid graph TD with step nodes and edges."""
        steps = [
            {"num": "1", "title": "Analyze"},
            {"num": "2", "title": "Implement"},
            {"num": "3", "title": "Verify"},
        ]
        result = generate_per_skill_mermaid("my-skill", steps)
        assert "```mermaid" in result
        assert "graph TD" in result
        assert "s1" in result
        assert "s2" in result
        assert "s3" in result
        # Sequential edges
        assert "s1 -->" in result
        assert "s2 -->" in result

    def test_gate_steps_are_diamonds(self):
        """Steps with has_gate=True should use diamond shape {{ }}."""
        steps = [
            {"num": "1", "title": "Check Gate", "has_gate": True},
            {"num": "2", "title": "Normal Step", "has_gate": False},
        ]
        result = generate_per_skill_mermaid("my-skill", steps)
        lines = result.split("\n")
        gate_line = [l for l in lines if "Check Gate" in l][0]
        normal_line = [l for l in lines if "Normal Step" in l][0]
        # Diamond uses { }, rectangle uses [ ]
        assert "{" in gate_line
        assert "[" in normal_line

    def test_delegations_shown_as_dashed_edges(self):
        """Skill/agent calls should appear as dashed edges to external nodes."""
        steps = [
            {"num": "1", "title": "Setup", "skill_calls": ["fix-loop"]},
            {"num": "2", "title": "Done"},
        ]
        result = generate_per_skill_mermaid("my-skill", steps)
        assert "fix-loop" in result
        assert "-.->" in result

    def test_empty_steps_returns_empty(self):
        """No steps means no diagram."""
        result = generate_per_skill_mermaid("my-skill", [])
        assert result == ""

    def test_backticks_sanitized_in_labels(self):
        """Backticks in titles must not break mermaid labels."""
        steps = [
            {"num": "1", "title": "Use `bun:test` Patterns"},
        ]
        result = generate_per_skill_mermaid("my-skill", steps)
        assert "`" not in result.split("```mermaid")[1].split("```")[0]


# ── generate_consolidated_step_flow tests ─────────────────────────


class TestGenerateConsolidatedStepFlow:
    """Tests for the consolidated cross-skill step flow diagram."""

    def test_basic_consolidated_flow(self):
        """Should produce a mermaid diagram stitching skill steps via delegations."""
        steps_a = [
            {"num": "1", "title": "Start A"},
            {"num": "2", "title": "Call B", "skill_calls": ["skill-b"]},
        ]
        steps_b = [
            {"num": "1", "title": "Start B"},
            {"num": "2", "title": "Finish B"},
        ]
        graph = _make_graph([("skill-a", steps_a), ("skill-b", steps_b)])
        workflow = _make_workflow(["skill-a", "skill-b"])
        result = generate_consolidated_step_flow(workflow, graph)

        assert "```mermaid" in result
        assert "graph TD" in result
        # Both skills should have subgraphs
        assert "skill-a" in result.lower().replace("_", "-") or "skill_a" in result
        assert "skill-b" in result.lower().replace("_", "-") or "skill_b" in result

    def test_cross_skill_delegation_edges(self):
        """Delegation from skill-a step to skill-b should create a cross-edge."""
        steps_a = [
            {"num": "1", "title": "Setup"},
            {"num": "2", "title": "Delegate", "skill_calls": ["skill-b"]},
        ]
        steps_b = [
            {"num": "1", "title": "Receive"},
            {"num": "2", "title": "Done"},
        ]
        graph = _make_graph([("skill-a", steps_a), ("skill-b", steps_b)])
        workflow = _make_workflow(["skill-a", "skill-b"])
        result = generate_consolidated_step_flow(workflow, graph)

        # Should have a cross-skill edge (thick arrow ==>)
        assert "==>" in result

    def test_empty_when_no_skills_have_steps(self):
        """If no skills have steps, return empty string."""
        graph = _make_graph([("empty", [])])
        workflow = _make_workflow(["empty"])
        result = generate_consolidated_step_flow(workflow, graph)
        assert result == ""

    def test_single_skill_still_renders(self):
        """Even one skill with steps should produce a diagram."""
        steps = [
            {"num": "1", "title": "Do A"},
            {"num": "2", "title": "Do B"},
        ]
        graph = _make_graph([("only-skill", steps)])
        workflow = _make_workflow(["only-skill"])
        result = generate_consolidated_step_flow(workflow, graph)
        assert "```mermaid" in result

    def test_capped_at_max_skills(self):
        """Workflows with too many stepped skills should return empty to avoid huge diagrams."""
        skill_names = [f"skill-{i}" for i in range(20)]
        skills_data = [
            (name, [{"num": "1", "title": "A"}, {"num": "2", "title": "B"}])
            for name in skill_names
        ]
        graph = _make_graph(skills_data)
        workflow = _make_workflow(skill_names)
        result = generate_consolidated_step_flow(workflow, graph)
        assert result == ""


# ── generate_entry_point_map tests ────────────────────────────────


class TestGenerateEntryPointMap:
    """Tests for the entry point map showing user-facing vs internal skills."""

    def test_identifies_entry_points(self):
        """Skills with no refs_in within the workflow are entry points."""
        graph = _make_graph([
            ("entry-skill", [{"num": "1", "title": "Start"}]),
            ("internal-skill", [{"num": "1", "title": "Work"}]),
        ])
        # entry-skill calls internal-skill, but nothing calls entry-skill
        graph["nodes"]["entry-skill"]["refs_out"] = ["internal-skill"]
        graph["nodes"]["internal-skill"]["refs_in"] = ["entry-skill"]
        graph["edges"] = [{"from": "entry-skill", "to": "internal-skill", "type": "Skill()"}]
        workflow = _make_workflow(
            ["entry-skill", "internal-skill"],
            edges=[{"from": "entry-skill", "to": "internal-skill", "type": "Skill()"}],
        )
        result = generate_entry_point_map(workflow, graph)

        assert "```mermaid" in result
        assert "entry-skill" in result.replace("_", "-")
        assert "internal-skill" in result.replace("_", "-")

    def test_entry_points_visually_distinct(self):
        """Entry point nodes should have a different shape than internal nodes."""
        graph = _make_graph([
            ("top-skill", [{"num": "1", "title": "Top"}]),
            ("mid-skill", [{"num": "1", "title": "Mid"}]),
        ])
        graph["nodes"]["top-skill"]["refs_out"] = ["mid-skill"]
        graph["nodes"]["mid-skill"]["refs_in"] = ["top-skill"]
        graph["edges"] = [{"from": "top-skill", "to": "mid-skill", "type": "Skill()"}]
        workflow = _make_workflow(
            ["top-skill", "mid-skill"],
            edges=[{"from": "top-skill", "to": "mid-skill", "type": "Skill()"}],
        )
        result = generate_entry_point_map(workflow, graph)
        lines = result.split("\n")

        # Entry point (top-skill) should use different shape than internal (mid-skill)
        top_lines = [l for l in lines if "top_skill" in l and ("[[" in l or "((" in l or "([" in l)]
        mid_lines = [l for l in lines if "mid_skill" in l and ("[/" in l or '["' in l)]
        assert len(top_lines) >= 1, "Entry point should have distinct shape"
        assert len(mid_lines) >= 1, "Internal node should have standard shape"

    def test_empty_when_no_edges(self):
        """No edges means no meaningful entry point distinction — return empty."""
        graph = _make_graph([("lone-skill", [{"num": "1", "title": "Solo"}])])
        workflow = _make_workflow(["lone-skill"])
        result = generate_entry_point_map(workflow, graph)
        assert result == ""

    def test_agents_included(self):
        """Agents dispatched by skills should appear in the entry point map."""
        graph = _make_graph([
            ("caller-skill", [{"num": "1", "title": "Call"}]),
        ])
        graph["nodes"]["my-agent"] = {
            "type": "agent",
            "path": "core/.claude/agents/my-agent.md",
            "description": "Test agent",
            "version": "1.0.0",
            "label": "core",
            "refs_out": [],
            "refs_in": ["caller-skill"],
            "steps": [],
        }
        graph["nodes"]["caller-skill"]["refs_out"] = ["my-agent"]
        graph["edges"] = [{"from": "caller-skill", "to": "my-agent", "type": "Agent()"}]
        workflow = _make_workflow(
            ["caller-skill"],
            edges=[{"from": "caller-skill", "to": "my-agent", "type": "Agent()"}],
        )
        workflow["agents"] = ["my-agent"]
        result = generate_entry_point_map(workflow, graph)

        assert "my-agent" in result.replace("_", "-")
