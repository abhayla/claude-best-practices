"""Generate workflow documentation by tracing skill/agent/rule interconnections.

Reads all SKILL.md, agent, and rule files in core/.claude/ and .claude/,
builds a cross-reference graph, and generates docs/workflows/*.md with
Mermaid diagrams, pattern tables, and interconnection maps.

Manual annotations below <!-- MANUAL ANNOTATIONS --> markers are preserved
across regeneration.

Usage:
    PYTHONPATH=. python scripts/generate_workflow_docs.py
    PYTHONPATH=. python scripts/generate_workflow_docs.py --dry-run
    PYTHONPATH=. python scripts/generate_workflow_docs.py --workflow testing-pipeline
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from scripts.workflow_quality_gate_validate_patterns import parse_frontmatter, get_body

ROOT = Path(__file__).parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
HUB_CLAUDE = ROOT / ".claude"
WORKFLOWS_DIR = ROOT / "docs" / "workflows"
GROUPS_CONFIG = ROOT / "config" / "workflow-groups.yml"

MANUAL_MARKER = "<!-- MANUAL ANNOTATIONS -->"


# ── Data Collection ─────────────────────────────────────────────


def collect_skills(base_dir: Path, label: str = "") -> dict[str, dict]:
    """Scan all SKILL.md files under base_dir/skills/."""
    skills = {}
    skills_dir = base_dir / "skills"
    if not skills_dir.exists():
        return skills
    for d in sorted(skills_dir.iterdir()):
        skill_md = d / "SKILL.md"
        if not d.is_dir() or not skill_md.exists():
            continue
        fm = parse_frontmatter(skill_md)
        body = get_body(skill_md)
        skills[d.name] = {
            "frontmatter": fm or {},
            "body": body,
            "path": str(skill_md.relative_to(ROOT)),
            "label": label,
        }
    return skills


def collect_agents(base_dir: Path, label: str = "") -> dict[str, dict]:
    """Scan all agent .md files under base_dir/agents/."""
    agents = {}
    agents_dir = base_dir / "agents"
    if not agents_dir.exists():
        return agents
    for f in sorted(agents_dir.iterdir()):
        if f.suffix == ".md" and f.name != "README.md":
            fm = parse_frontmatter(f)
            body = get_body(f)
            agents[f.stem] = {
                "frontmatter": fm or {},
                "body": body,
                "path": str(f.relative_to(ROOT)),
                "label": label,
            }
    return agents


def collect_rules(base_dir: Path, label: str = "") -> dict[str, dict]:
    """Scan all rule .md files under base_dir/rules/."""
    rules = {}
    rules_dir = base_dir / "rules"
    if not rules_dir.exists():
        return rules
    for f in sorted(rules_dir.iterdir()):
        if f.suffix == ".md" and f.name != "README.md":
            fm = parse_frontmatter(f)
            body = get_body(f)
            rules[f.stem] = {
                "frontmatter": fm or {},
                "body": body,
                "path": str(f.relative_to(ROOT)),
                "label": label,
            }
    return rules


# ── Reference Tracing ──────────────────────────────────────────


def extract_references(name: str, body: str) -> dict:
    """Extract all outgoing cross-references from a pattern's body."""
    refs = {
        "skill_calls": set(),
        "agent_calls": set(),
    }

    # Skill("name") or Skill('name')
    for m in re.finditer(r'Skill\(["\']([a-z0-9_-]+)["\']\)', body):
        refs["skill_calls"].add(m.group(1))

    # /skill-name in backticks: `/fix-loop`, `/learn-n-improve`
    for m in re.finditer(r'`/([a-z0-9_-]+)`', body):
        refs["skill_calls"].add(m.group(1))

    # Agent("name") or Agent('name')
    for m in re.finditer(r'Agent\(["\']([a-z0-9_-]+)["\']\)', body):
        refs["agent_calls"].add(m.group(1))

    # "delegate to /name" or "delegates to /name"
    for m in re.finditer(r'delegates?\s+to\s+`?/([a-z0-9_-]+)`?', body, re.IGNORECASE):
        refs["skill_calls"].add(m.group(1))

    # "invoke /name" or "invokes /name" or "run /name"
    for m in re.finditer(r'(?:invokes?|runs?)\s+`?/([a-z0-9_-]+)`?', body, re.IGNORECASE):
        refs["skill_calls"].add(m.group(1))

    # Prose agent references: "delegate to docs-manager-agent",
    # "via tester-agent", "dispatches test-failure-analyzer-agent"
    for m in re.finditer(r'[Dd]elegates?\s+to\s+([a-z][a-z0-9-]*-agent)', body):
        refs["agent_calls"].add(m.group(1))
    for m in re.finditer(r'[Dd]ispatche?s?\s+([a-z][a-z0-9-]*-agent)', body):
        refs["agent_calls"].add(m.group(1))
    for m in re.finditer(r'via\s+([a-z][a-z0-9-]*-agent)', body):
        refs["agent_calls"].add(m.group(1))
    # Backtick-quoted agent names
    for m in re.finditer(r'`([a-z][a-z0-9-]*-agent)`', body):
        refs["agent_calls"].add(m.group(1))

    # Multi-reference delegation: catch all `/skill` refs on delegation lines
    for line in body.splitlines():
        if re.search(r'[Dd]elegates?\s+to', line):
            for sm in re.finditer(r'`/([a-z0-9_-]+)`', line):
                refs["skill_calls"].add(sm.group(1))

    # Remove self-references
    refs["skill_calls"].discard(name)
    refs["agent_calls"].discard(name)

    return {k: sorted(v) for k, v in refs.items()}


def extract_steps(name: str, body: str) -> list[dict]:
    """Extract numbered STEP sections from a skill body.

    Returns a list of step dicts with title, delegations, gates, artifacts,
    and decision points.
    """
    steps = []
    # Match ## STEP N: Title or ## STEP N — Title
    step_pattern = re.compile(
        r'^##\s+STEP\s+(\d+\w*)\s*[:\-—]\s*(.+)', re.MULTILINE
    )
    matches = list(step_pattern.finditer(body))
    if not matches:
        return steps

    for i, m in enumerate(matches):
        step_num = m.group(1).strip()
        step_title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section = body[start:end]

        # Extract delegations within this step
        skill_calls = set()
        for sm in re.finditer(r'Skill\(["\']([a-z0-9_-]+)["\']\)', section):
            skill_calls.add(sm.group(1))
        for sm in re.finditer(r'`/([a-z0-9_-]+)`', section):
            skill_calls.add(sm.group(1))
        skill_calls.discard(name)

        agent_calls = set()
        for am in re.finditer(r'Agent\(["\']([a-z0-9_-]+)["\']\)', section):
            agent_calls.add(am.group(1))

        # Prose agent references: "delegate to docs-manager-agent",
        # "via tester-agent", "dispatches test-failure-analyzer-agent"
        prose_agent_patterns = [
            r'[Dd]elegates?\s+to\s+([a-z][a-z0-9-]*-agent)',
            r'via\s+([a-z][a-z0-9-]*-agent)',
            r'[Dd]ispatche?s?\s+([a-z][a-z0-9-]*-agent)',
            r'`([a-z][a-z0-9-]*-agent)`',
        ]
        for pat in prose_agent_patterns:
            for pam in re.finditer(pat, section):
                agent_calls.add(pam.group(1))

        # Multi-reference delegation: "/skill-a or /skill-b"
        # Catch backtick-quoted skill refs after "or"/"and" on delegation lines
        for line in section.splitlines():
            if re.search(r'[Dd]elegates?\s+to', line):
                for sm in re.finditer(r'`/([a-z0-9_-]+)`', line):
                    ref = sm.group(1)
                    if ref != name:
                        skill_calls.add(ref)

        # Detect gate checks
        has_gate = bool(re.search(
            r'(?:gate|block|BLOCK|reads?\s+.*\.json|upstream)', section, re.IGNORECASE
        ))

        # Detect decision points
        has_decision = bool(re.search(
            r'(?:if\s+.*(?:fail|pass|exist|missing)|→.*mode|→.*BLOCK)',
            section, re.IGNORECASE
        ))

        # Detect artifact production (deduplicated)
        artifacts_set = set()
        for am in re.finditer(r'(?:test-results|test-evidence)/[a-z0-9_\-{}/.*]+\.json', section):
            artifacts_set.add(am.group(0))
        artifacts = sorted(artifacts_set)

        # Detect artifact consumption (reads/gates on upstream JSON)
        artifacts_consumed = set()
        consume_patterns = [
            r'[Rr]ead[s]?\s+`?(test-(?:results|evidence)/[a-z0-9_\-{}/.*]+\.json)`?',
            r'[Ii]f\s+`?(test-(?:results|evidence)/[a-z0-9_\-{}/.*]+\.json)`?\s+exists',
            r'-f\s+(test-(?:results|evidence)/[a-z0-9_\-{}/.*]+\.json)',
            r'from\s+`?(test-(?:results|evidence)/[a-z0-9_\-{}/.*]+\.json)`?',
        ]
        for pat in consume_patterns:
            for cm in re.finditer(pat, section):
                artifacts_consumed.add(cm.group(1))

        # Extract branch targets from decision points
        branches = []
        branch_patterns = [
            # → BLOCK or → BLOCK.
            (r'→\s*(BLOCK)', "BLOCK"),
            # → proceed to STEP N or → STEP N
            (r'→\s*(?:proceed to\s+)?STEP\s+(\d+\w*)', None),
            # if ... PASSED/FAILED → ...
            (r'[Ii]f\s+.*?(PASSED|FIXED)\s*→', "PASS"),
            (r'[Ii]f\s+.*?(FAILED|FLAKY)\s*→', "FAIL"),
        ]
        for pat, label_override in branch_patterns:
            for bm in re.finditer(pat, section):
                branch_label = label_override or f"STEP {bm.group(1)}"
                if branch_label not in [b["label"] for b in branches]:
                    branches.append({"label": branch_label})

        steps.append({
            "num": step_num,
            "title": step_title,
            "skill_calls": sorted(skill_calls),
            "agent_calls": sorted(agent_calls),
            "has_gate": has_gate,
            "has_decision": has_decision,
            "artifacts": artifacts,
            "artifacts_consumed": sorted(artifacts_consumed),
            "branches": branches,
        })

    return steps


def build_reference_graph(
    skills: dict, agents: dict, rules: dict
) -> dict:
    """Build a bidirectional adjacency graph of all cross-references."""
    nodes = {}
    edges = []

    all_patterns = {}
    for name, data in skills.items():
        all_patterns[name] = ("skill", data)
    for name, data in agents.items():
        all_patterns[name] = ("agent", data)
    for name, data in rules.items():
        all_patterns[name] = ("rule", data)

    # Initialize nodes
    for name, (ptype, data) in all_patterns.items():
        steps = extract_steps(name, data["body"]) if ptype == "skill" else []
        nodes[name] = {
            "type": ptype,
            "path": data["path"],
            "description": data["frontmatter"].get("description", ""),
            "version": data["frontmatter"].get("version", ""),
            "label": data.get("label", ""),
            "refs_out": [],
            "refs_in": [],
            "steps": steps,
        }

    # Extract references and build edges
    for name, (ptype, data) in all_patterns.items():
        refs = extract_references(name, data["body"])

        for target in refs["skill_calls"]:
            if target in nodes:
                edge = {"from": name, "to": target, "type": "Skill()"}
                edges.append(edge)
                nodes[name]["refs_out"].append(target)
                nodes[target]["refs_in"].append(name)

        for target in refs["agent_calls"]:
            if target in nodes:
                edge = {"from": name, "to": target, "type": "Agent()"}
                edges.append(edge)
                nodes[name]["refs_out"].append(target)
                nodes[target]["refs_in"].append(name)

    return {"nodes": nodes, "edges": edges}


# ── Workflow Grouping ──────────────────────────────────────────


def load_workflow_definitions() -> dict:
    """Load workflow group definitions from config/workflow-groups.yml."""
    if not GROUPS_CONFIG.exists():
        print(f"ERROR: {GROUPS_CONFIG} not found", file=sys.stderr)
        sys.exit(1)
    with open(GROUPS_CONFIG, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("workflows", {})


def assign_patterns_to_workflows(
    graph: dict, definitions: dict
) -> dict[str, dict]:
    """Assign patterns to workflow groups using seeds from config."""
    workflows = {}

    for wf_name, wf_def in definitions.items():
        seeds = wf_def.get("seeds", {})
        seed_skills = set(seeds.get("skills", []))
        seed_agents = set(seeds.get("agents", []))
        seed_rules = set(seeds.get("rules", []))

        all_members = seed_skills | seed_agents | seed_rules

        # Walk one level of the reference graph from seeds
        discovered = set()
        for member in all_members:
            node = graph["nodes"].get(member)
            if not node:
                continue
            for ref in node["refs_out"]:
                ref_node = graph["nodes"].get(ref)
                if ref_node and ref_node["type"] in ("skill", "agent"):
                    discovered.add(ref)

        final_skills = set()
        final_agents = set()
        final_rules = set()

        for name in all_members | discovered:
            node = graph["nodes"].get(name)
            if not node:
                continue
            if node["type"] == "skill":
                final_skills.add(name)
            elif node["type"] == "agent":
                final_agents.add(name)
            elif node["type"] == "rule":
                final_rules.add(name)

        # Collect edges within this workflow
        wf_members = final_skills | final_agents | final_rules
        wf_edges = [
            e for e in graph["edges"]
            if e["from"] in wf_members and e["to"] in wf_members
        ]

        workflows[wf_name] = {
            "description": wf_def.get("description", ""),
            "skills": sorted(final_skills),
            "agents": sorted(final_agents),
            "rules": sorted(final_rules),
            "edges": wf_edges,
        }

    return workflows


def find_orphan_patterns(graph: dict, workflows: dict) -> list[str]:
    """Find patterns not assigned to any workflow group."""
    assigned = set()
    for wf in workflows.values():
        assigned.update(wf["skills"])
        assigned.update(wf["agents"])
        assigned.update(wf["rules"])

    orphans = []
    for name, node in graph["nodes"].items():
        if name not in assigned:
            orphans.append(f"{name} ({node['type']})")
    return sorted(orphans)


# ── Mermaid Generation ─────────────────────────────────────────


def generate_mermaid_flow(workflow: dict) -> str:
    """Generate a Mermaid flowchart for a single workflow."""
    lines = ["```mermaid", "graph LR"]

    # Define node shapes: skills=rectangles, agents=rounded, rules=hexagons
    all_names = set()
    for name in workflow["skills"]:
        safe = name.replace("-", "_")
        lines.append(f"    {safe}[/{name}/]")
        all_names.add(name)
    for name in workflow["agents"]:
        safe = name.replace("-", "_")
        lines.append(f"    {safe}([{name}])")
        all_names.add(name)
    for name in workflow["rules"]:
        safe = name.replace("-", "_")
        lines.append(f"    {safe}{{{{{name}}}}}")
        all_names.add(name)

    # Add edges
    seen_edges = set()
    for edge in workflow["edges"]:
        src = edge["from"].replace("-", "_")
        tgt = edge["to"].replace("-", "_")
        key = f"{src}->{tgt}"
        if key not in seen_edges:
            lines.append(f"    {src} --> {tgt}")
            seen_edges.add(key)

    lines.append("```")
    return "\n".join(lines)


def generate_detailed_mermaid(workflow: dict, graph: dict) -> str:
    """Generate a detailed Mermaid flowchart showing steps, gates, and artifacts.

    For each skill that has extracted steps, shows the step-level flow with
    decision diamonds for gates and artifact nodes for JSON outputs.
    Only includes skills with 3+ steps to avoid noise.
    """
    lines = ["```mermaid", "graph TD"]
    node_ids = set()

    # Collect skills with meaningful step data
    detailed_skills = []
    for sname in workflow["skills"]:
        node = graph["nodes"].get(sname, {})
        steps = node.get("steps", [])
        if len(steps) >= 3:
            detailed_skills.append((sname, steps))

    if not detailed_skills:
        return ""

    for sname, steps in detailed_skills:
        safe_skill = sname.replace("-", "_")

        # Subgraph per skill
        display = sname.replace("-", " ").title()
        lines.append(f"    subgraph {safe_skill}_sub[\"{display}\"]")

        prev_id = None
        for step in steps:
            step_id = f"{safe_skill}_s{step['num']}"
            label = f"Step {step['num']}: {step['title']}"
            node_ids.add(step_id)

            if step["has_gate"]:
                # Diamond for gate/decision
                lines.append(f"        {step_id}{{{{{label}}}}}")
            else:
                lines.append(f"        {step_id}[\"{label}\"]")

            if prev_id:
                # If previous step had branches, label the forward edge as PASS
                prev_step = next(
                    (s for s in steps if f"{safe_skill}_s{s['num']}" == prev_id),
                    None
                )
                has_block_branch = prev_step and any(
                    b["label"] == "BLOCK" for b in prev_step.get("branches", [])
                )
                if has_block_branch:
                    lines.append(f"        {prev_id} -->|OK| {step_id}")
                else:
                    lines.append(f"        {prev_id} --> {step_id}")
            prev_id = step_id

            # Show delegations as edges to external nodes
            for sc in step["skill_calls"]:
                ext_id = sc.replace("-", "_") + "_ext"
                if ext_id not in node_ids:
                    lines.append(f"        {ext_id}([/{sc}/])")
                    node_ids.add(ext_id)
                lines.append(f"        {step_id} -.-> {ext_id}")

            for ac in step["agent_calls"]:
                ext_id = ac.replace("-", "_") + "_ext"
                if ext_id not in node_ids:
                    lines.append(f"        {ext_id}(({ac}))")
                    node_ids.add(ext_id)
                lines.append(f"        {step_id} -.-> {ext_id}")

            # Show artifact consumption (dashed arrow FROM artifact TO step)
            for art in step.get("artifacts_consumed", []):
                art_id = (
                    safe_skill + "_" +
                    art.replace("/", "_").replace(".", "_").replace("-", "_")
                    .replace("{", "").replace("}", "").replace("*", "")
                )
                if art_id not in node_ids:
                    lines.append(f"        {art_id}[(\"{art}\")]")
                    node_ids.add(art_id)
                lines.append(f"        {art_id} -.->|reads| {step_id}")

            # Show artifact production (solid arrow FROM step TO artifact)
            for art in step["artifacts"]:
                # Skip if already shown as consumed (avoid duplicate nodes)
                if art in step.get("artifacts_consumed", []):
                    continue
                art_id = (
                    safe_skill + "_" +
                    art.replace("/", "_").replace(".", "_").replace("-", "_")
                    .replace("{", "").replace("}", "").replace("*", "")
                )
                if art_id not in node_ids:
                    lines.append(f"        {art_id}[(\"{art}\")]")
                    node_ids.add(art_id)
                lines.append(f"        {step_id} -->|writes| {art_id}")

            # Show branch labels on decision steps
            for branch in step.get("branches", []):
                label = branch["label"]
                if label == "BLOCK":
                    block_id = f"{step_id}_block"
                    if block_id not in node_ids:
                        lines.append(f"        {block_id}[/BLOCK/]")
                        node_ids.add(block_id)
                    lines.append(
                        f"        {step_id} -->|FAILED| {block_id}"
                    )

        lines.append("    end")
        lines.append("")

    # Add inter-skill edges for the detailed skills
    detailed_names = {s[0] for s in detailed_skills}
    for edge in workflow["edges"]:
        if edge["from"] in detailed_names and edge["to"] in detailed_names:
            src_sub = edge["from"].replace("-", "_") + "_sub"
            tgt_sub = edge["to"].replace("-", "_") + "_sub"
            # Don't duplicate — subgraph-to-subgraph edges
            # Instead, find the step that makes the call and connect
            src_node = graph["nodes"].get(edge["from"], {})
            for step in src_node.get("steps", []):
                target = edge["to"]
                if target in step["skill_calls"] or target in step["agent_calls"]:
                    src_id = f"{edge['from'].replace('-', '_')}_s{step['num']}"
                    # Find first step of target
                    tgt_node = graph["nodes"].get(edge["to"], {})
                    tgt_steps = tgt_node.get("steps", [])
                    if tgt_steps:
                        tgt_id = f"{edge['to'].replace('-', '_')}_s{tgt_steps[0]['num']}"
                        edge_key = f"{src_id}-->{tgt_id}"
                        if edge_key not in node_ids:
                            lines.append(f"    {src_id} ==> {tgt_id}")
                            node_ids.add(edge_key)
                    break

    lines.append("```")

    # Only return if we generated meaningful content
    if len(lines) <= 3:
        return ""
    return "\n".join(lines)


def generate_cross_workflow_mermaid(workflows: dict, graph: dict) -> str:
    """Generate a top-level cross-workflow connection diagram."""
    lines = ["```mermaid", "graph TD"]

    wf_ids = {}
    for wf_name in workflows:
        safe = wf_name.replace("-", "_")
        display = wf_name.replace("-", " ").title()
        lines.append(f"    {safe}[{display}]")
        wf_ids[wf_name] = safe

    # Find cross-workflow edges
    wf_membership = {}
    for wf_name, wf in workflows.items():
        for name in wf["skills"] + wf["agents"] + wf["rules"]:
            wf_membership.setdefault(name, set()).add(wf_name)

    cross_edges = set()
    for edge in graph["edges"]:
        src_wfs = wf_membership.get(edge["from"], set())
        tgt_wfs = wf_membership.get(edge["to"], set())
        for sw in src_wfs:
            for tw in tgt_wfs:
                if sw != tw:
                    key = (sw, tw)
                    if key not in cross_edges:
                        cross_edges.add(key)
                        lines.append(
                            f"    {wf_ids[sw]} --> {wf_ids[tw]}"
                        )

    lines.append("```")
    return "\n".join(lines)


# ── Markdown Rendering ─────────────────────────────────────────


def preserve_manual_annotations(existing_content: str) -> str:
    """Extract user-written content below the MANUAL ANNOTATIONS marker.

    Strips the marker itself and the auto-generated comment line that follows it,
    returning only genuine user annotations.
    """
    if MANUAL_MARKER not in existing_content:
        return ""
    idx = existing_content.index(MANUAL_MARKER)
    after = existing_content[idx + len(MANUAL_MARKER):]
    # Remove auto-generated instruction comments
    lines = after.splitlines()
    filtered = [
        line for line in lines
        if not line.strip().startswith("<!-- Add custom notes")
    ]
    return "\n".join(filtered).strip()


def render_workflow_doc(
    name: str,
    workflow: dict,
    graph: dict,
    existing_content: Optional[str] = None,
) -> str:
    """Render a single workflow markdown file."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    display_name = name.replace("-", " ").title()

    lines = [
        f"# {display_name}",
        "",
        f"> {workflow['description']}",
        "",
        f"> Auto-generated by `scripts/generate_workflow_docs.py` | Last updated: {now}",
        "",
    ]

    # Overview diagram (skill-to-skill edges)
    if workflow["edges"]:
        lines.extend(["## Overview", ""])
        lines.append(generate_mermaid_flow(workflow))
        lines.append("")

    # Detailed diagram (step-level with gates, artifacts, decisions)
    detailed = generate_detailed_mermaid(workflow, graph)
    if detailed:
        lines.extend(["## Detailed Flow", ""])
        lines.append(
            "Step-level flow showing gates (diamonds), delegations (dashed), "
            "and artifacts (cylinders)."
        )
        lines.append("")
        lines.append(detailed)
        lines.append("")

    # Skills table
    if workflow["skills"]:
        lines.extend([
            "## Skills",
            "",
            "| Skill | Version | Description | Calls | Called By |",
            "|-------|---------|-------------|-------|----------|",
        ])
        for sname in workflow["skills"]:
            node = graph["nodes"].get(sname, {})
            version = node.get("version", "—")
            desc = node.get("description", "—")
            if isinstance(desc, str) and len(desc) > 80:
                desc = desc[:77] + "..."
            refs_out = [r for r in node.get("refs_out", []) if r in
                        set(workflow["skills"] + workflow["agents"])]
            refs_in = [r for r in node.get("refs_in", []) if r in
                       set(workflow["skills"] + workflow["agents"])]
            calls = ", ".join(f"`/{r}`" for r in refs_out) or "—"
            called_by = ", ".join(f"`/{r}`" for r in refs_in) or "—"
            lines.append(f"| `/{sname}` | {version} | {desc} | {calls} | {called_by} |")
        lines.append("")

    # Agents table
    if workflow["agents"]:
        lines.extend([
            "## Agents",
            "",
            "| Agent | Description | Dispatched By |",
            "|-------|-------------|---------------|",
        ])
        for aname in workflow["agents"]:
            node = graph["nodes"].get(aname, {})
            desc = node.get("description", "—")
            if isinstance(desc, str) and len(desc) > 80:
                desc = desc[:77] + "..."
            refs_in = [r for r in node.get("refs_in", [])
                       if r in set(workflow["skills"] + workflow["agents"])]
            dispatched = ", ".join(f"`/{r}`" for r in refs_in) or "—"
            lines.append(f"| `{aname}` | {desc} | {dispatched} |")
        lines.append("")

    # Rules table
    if workflow["rules"]:
        lines.extend([
            "## Rules",
            "",
            "| Rule | Description |",
            "|------|-------------|",
        ])
        for rname in workflow["rules"]:
            node = graph["nodes"].get(rname, {})
            desc = node.get("description", "—")
            if isinstance(desc, str) and len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(f"| `{rname}` | {desc} |")
        lines.append("")

    # Cross-workflow connections
    all_members = set(workflow["skills"] + workflow["agents"] + workflow["rules"])
    outgoing = set()
    incoming = set()
    for edge in graph["edges"]:
        if edge["from"] in all_members and edge["to"] not in all_members:
            outgoing.add(edge["to"])
        if edge["to"] in all_members and edge["from"] not in all_members:
            incoming.add(edge["from"])

    if outgoing or incoming:
        lines.extend(["## Cross-Workflow Connections", ""])
        if outgoing:
            lines.append("**Outgoing** (this workflow feeds into):")
            for target in sorted(outgoing):
                node = graph["nodes"].get(target, {})
                lines.append(f"- `{target}` ({node.get('type', '?')})")
            lines.append("")
        if incoming:
            lines.append("**Incoming** (fed by):")
            for source in sorted(incoming):
                node = graph["nodes"].get(source, {})
                lines.append(f"- `{source}` ({node.get('type', '?')})")
            lines.append("")

    # Manual annotations
    lines.extend([
        MANUAL_MARKER,
        "<!-- Add custom notes below this line. They are preserved on regeneration. -->",
        "",
    ])

    if existing_content:
        manual = preserve_manual_annotations(existing_content)
        if manual:
            lines.append(manual)
            lines.append("")

    return "\n".join(lines)


def render_index(workflows: dict, graph: dict, orphans: list[str]) -> str:
    """Render the INDEX.md file."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Workflow Documentation",
        "",
        f"> Auto-generated by `scripts/generate_workflow_docs.py` | Last updated: {now}",
        "",
        "## Workflows",
        "",
        "| Workflow | Skills | Agents | Rules | Description |",
        "|----------|--------|--------|-------|-------------|",
    ]

    for wf_name, wf in sorted(workflows.items()):
        display = wf_name.replace("-", " ").title()
        link = f"[{display}]({wf_name}.md)"
        lines.append(
            f"| {link} | {len(wf['skills'])} | {len(wf['agents'])} | "
            f"{len(wf['rules'])} | {wf['description']} |"
        )

    lines.extend(["", "## Cross-Workflow Connections", ""])
    lines.append(generate_cross_workflow_mermaid(workflows, graph))
    lines.append("")

    if orphans:
        lines.extend([
            "## Orphan Patterns",
            "",
            "These patterns are not assigned to any workflow group.",
            "Add them to `config/workflow-groups.yml` if they belong to a workflow.",
            "",
        ])
        for orphan in orphans:
            lines.append(f"- {orphan}")
        lines.append("")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate workflow documentation from pattern cross-references."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing files."
    )
    parser.add_argument(
        "--workflow", type=str, default=None,
        help="Regenerate only a specific workflow doc."
    )
    args = parser.parse_args()

    # 0. Auto-assign orphan patterns before generating docs
    assign_script = ROOT / "scripts" / "assign_workflow_groups.py"
    if assign_script.exists():
        import os
        env = {**os.environ, "PYTHONPATH": str(ROOT)}
        subprocess.run([sys.executable, str(assign_script)], check=True, env=env)

    # 1. Collect all patterns from both core and hub-only dirs
    skills = collect_skills(CORE_CLAUDE, label="core")
    skills.update(collect_skills(HUB_CLAUDE, label="hub-only"))

    agents = collect_agents(CORE_CLAUDE, label="core")
    agents.update(collect_agents(HUB_CLAUDE, label="hub-only"))

    rules = collect_rules(CORE_CLAUDE, label="core")
    rules.update(collect_rules(HUB_CLAUDE, label="hub-only"))

    print(f"Collected: {len(skills)} skills, {len(agents)} agents, {len(rules)} rules")

    # 2. Build reference graph
    graph = build_reference_graph(skills, agents, rules)
    edge_count = len(graph["edges"])
    print(f"Reference graph: {len(graph['nodes'])} nodes, {edge_count} edges")

    # 3. Load workflow definitions
    definitions = load_workflow_definitions()
    if args.workflow:
        if args.workflow not in definitions:
            print(f"ERROR: Unknown workflow '{args.workflow}'. "
                  f"Available: {', '.join(definitions.keys())}", file=sys.stderr)
            sys.exit(1)
        definitions = {args.workflow: definitions[args.workflow]}

    # 4. Assign patterns to workflows
    workflows = assign_patterns_to_workflows(graph, definitions)

    # 5. Find orphans (only when generating all)
    orphans = []
    if not args.workflow:
        orphans = find_orphan_patterns(graph, workflows)

    # 6. Generate/update docs
    if not args.dry_run:
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    for wf_name, wf_data in sorted(workflows.items()):
        doc_path = WORKFLOWS_DIR / f"{wf_name}.md"

        existing = None
        if doc_path.exists():
            existing = doc_path.read_text(encoding="utf-8")

        content = render_workflow_doc(wf_name, wf_data, graph, existing)

        if args.dry_run:
            status = "UPDATE" if existing else "CREATE"
            print(f"  [{status}] docs/workflows/{wf_name}.md "
                  f"({len(wf_data['skills'])} skills, {len(wf_data['agents'])} agents, "
                  f"{len(wf_data['rules'])} rules)")
        else:
            doc_path.write_text(content, encoding="utf-8")
            status = "Updated" if existing else "Created"
            print(f"  {status}: docs/workflows/{wf_name}.md")

        generated.append(wf_name)

    # 7. Generate index (only when generating all)
    if not args.workflow:
        index_content = render_index(workflows, graph, orphans)
        index_path = WORKFLOWS_DIR / "INDEX.md"
        if args.dry_run:
            print(f"  [{'UPDATE' if index_path.exists() else 'CREATE'}] "
                  f"docs/workflows/INDEX.md")
        else:
            index_path.write_text(index_content, encoding="utf-8")
            print(f"  {'Updated' if index_path.exists() else 'Created'}: "
                  f"docs/workflows/INDEX.md")

    # 8. Summary
    print(f"\nGenerated {len(generated)} workflow docs.")
    if orphans:
        print(f"Orphan patterns ({len(orphans)}): {', '.join(orphans[:10])}")
        if len(orphans) > 10:
            print(f"  ... and {len(orphans) - 10} more")


if __name__ == "__main__":
    main()
