"""Auto-assign orphan core/ patterns to workflow groups.

Scores each orphan against existing workflow groups using:
  - Reference graph overlap (weight: 3 per match)
  - Keyword similarity in name/description (weight: 1 per match)

Updates config/workflow-groups.yml only if assignments change.

Usage:
    PYTHONPATH=. python scripts/assign_workflow_groups.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

from scripts.generate_workflow_docs import (
    ROOT,
    CORE_CLAUDE,
    GROUPS_CONFIG,
    collect_skills,
    collect_agents,
    collect_rules,
    build_reference_graph,
    load_workflow_definitions,
)

NEEDS_REVIEW_GROUP = "_needs-manual-review"

STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on",
    "is", "it", "with", "that", "this", "by", "as", "at", "from",
    "be", "are", "was", "were", "been", "use", "when", "run",
})


def get_all_seeds(definitions: dict) -> dict[str, set[str]]:
    """Return {group_name: set_of_seed_names} for all groups."""
    result = {}
    for wf_name, wf_def in definitions.items():
        seeds = wf_def.get("seeds", {})
        all_names = set()
        for category in ("skills", "agents", "rules"):
            all_names.update(seeds.get(category, []))
        result[wf_name] = all_names
    return result


def find_orphans(definitions: dict, all_patterns: set[str]) -> set[str]:
    """Find patterns not seeded in any workflow group."""
    seeded = set()
    for wf_def in definitions.values():
        seeds = wf_def.get("seeds", {})
        for category in ("skills", "agents", "rules"):
            seeded.update(seeds.get(category, []))
    return all_patterns - seeded


def score_reference_graph(
    orphan: str, group_seeds: set[str], graph: dict
) -> int:
    """Score based on reference graph overlap (3 points per match)."""
    node = graph["nodes"].get(orphan)
    if not node:
        return 0
    connections = set(node["refs_out"]) | set(node["refs_in"])
    return len(connections & group_seeds) * 3


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase tokens, removing stop words."""
    tokens = set(re.split(r"[-_\s,.:;()/]+", text.lower()))
    return tokens - STOP_WORDS - {""}


def score_keywords(
    orphan: str,
    orphan_desc: str,
    group_name: str,
    group_desc: str,
    group_seeds: set[str],
) -> int:
    """Score based on keyword overlap in name/description (1 point per match)."""
    group_words = _tokenize(group_name) | _tokenize(group_desc)
    for seed in group_seeds:
        group_words |= _tokenize(seed)

    orphan_words = _tokenize(orphan) | _tokenize(orphan_desc)
    return len(orphan_words & group_words)


def compute_assignments(
    orphans: set[str], definitions: dict, graph: dict
) -> dict[str, list[tuple[str, str, int]]]:
    """Compute best workflow group(s) for each orphan.

    Returns {group_name: [(pattern_name, pattern_type, score), ...]}.
    """
    group_seeds = get_all_seeds(definitions)
    assignments: dict[str, list[tuple[str, str, int]]] = {
        name: [] for name in definitions
    }
    assignments[NEEDS_REVIEW_GROUP] = []

    for orphan in sorted(orphans):
        node = graph["nodes"].get(orphan)
        if not node:
            continue
        orphan_desc = node.get("description", "")
        ptype = node["type"]

        scores: dict[str, int] = {}
        for wf_name, wf_def in definitions.items():
            if wf_name == NEEDS_REVIEW_GROUP:
                continue
            ref_score = score_reference_graph(orphan, group_seeds[wf_name], graph)
            kw_score = score_keywords(
                orphan,
                orphan_desc,
                wf_name,
                wf_def.get("description", ""),
                group_seeds[wf_name],
            )
            scores[wf_name] = ref_score + kw_score

        top_score = max(scores.values()) if scores else 0

        if top_score == 0:
            assignments[NEEDS_REVIEW_GROUP].append((orphan, ptype, 0))
        elif top_score < 4:
            # Low confidence: assign to the single best group only
            best_group = max(scores, key=scores.get)
            assignments[best_group].append((orphan, ptype, top_score))
        else:
            # High confidence: assign to top group + any others within 1 point
            threshold = top_score - 1
            for wf_name, score in scores.items():
                if score >= threshold:
                    assignments[wf_name].append((orphan, ptype, score))

    return assignments


def _build_yaml_output(definitions: dict) -> str:
    """Build workflow-groups.yml content with sorted seeds."""
    lines = [
        "# Workflow group definitions for generate_workflow_docs.py",
        "#",
        "# Each group has seed patterns (anchors) and a description.",
        "# The script walks the reference graph from seeds to discover",
        "# connected patterns. Patterns can appear in multiple groups.",
        "#",
        "# To add a new workflow group: add an entry here, then run",
        "# /update-workflow-docs to regenerate docs/workflows/.",
        "",
        "workflows:",
    ]

    for wf_name, wf_def in definitions.items():
        lines.append(f"  {wf_name}:")
        desc = wf_def.get("description", "")
        lines.append(f'    description: "{desc}"')
        lines.append("    seeds:")

        seeds = wf_def.get("seeds", {})
        for category in ("skills", "agents", "rules"):
            seed_list = sorted(seeds.get(category, []))
            if not seed_list:
                lines.append(f"      {category}: []")
            else:
                lines.append(f"      {category}:")
                for name in seed_list:
                    lines.append(f"        - {name}")

        lines.append("")

    return "\n".join(lines) + "\n"


def update_workflow_groups_yaml(
    definitions: dict, assignments: dict, dry_run: bool = False
) -> bool:
    """Update workflow-groups.yml with new assignments. Returns True if changed."""
    original = GROUPS_CONFIG.read_text(encoding="utf-8")

    if NEEDS_REVIEW_GROUP not in definitions and assignments.get(NEEDS_REVIEW_GROUP):
        definitions[NEEDS_REVIEW_GROUP] = {
            "description": "Patterns that could not be auto-assigned. Requires manual review.",
            "seeds": {"skills": [], "agents": [], "rules": []},
        }

    for wf_name, new_entries in assignments.items():
        if not new_entries or wf_name not in definitions:
            continue
        seeds = definitions[wf_name].setdefault("seeds", {})
        for pattern_name, ptype, _score in new_entries:
            category = ptype + "s"
            seed_list = seeds.setdefault(category, [])
            if pattern_name not in seed_list:
                seed_list.append(pattern_name)

    new_content = _build_yaml_output(definitions)

    if new_content.rstrip() == original.rstrip():
        return False

    if not dry_run:
        GROUPS_CONFIG.write_text(new_content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Auto-assign orphan core/ patterns to workflow groups."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show assignments without writing.",
    )
    args = parser.parse_args()

    skills = collect_skills(CORE_CLAUDE, label="core")
    agents = collect_agents(CORE_CLAUDE, label="core")
    rules = collect_rules(CORE_CLAUDE, label="core")
    print(f"Core patterns: {len(skills)} skills, {len(agents)} agents, {len(rules)} rules")

    all_pattern_names = set(skills.keys()) | set(agents.keys()) | set(rules.keys())

    graph = build_reference_graph(skills, agents, rules)

    definitions = load_workflow_definitions()

    orphans = find_orphans(definitions, all_pattern_names)
    print(f"Orphans: {len(orphans)}")

    if not orphans:
        print("No orphans found. Nothing to do.")
        return

    assignments = compute_assignments(orphans, definitions, graph)

    total_assigned = 0
    for wf_name, entries in sorted(assignments.items()):
        if not entries:
            continue
        if wf_name == NEEDS_REVIEW_GROUP:
            print(f"\n  {NEEDS_REVIEW_GROUP}: {len(entries)} patterns")
        else:
            high = [e for e in entries if e[2] >= 4]
            low = [e for e in entries if e[2] < 4]
            print(
                f"  {wf_name}: +{len(entries)} "
                f"({len(high)} high-confidence, {len(low)} low-confidence)"
            )
        for name, ptype, score in entries:
            confidence = "HIGH" if score >= 4 else "LOW" if score > 0 else "NONE"
            print(f"    {name} ({ptype}) score={score} [{confidence}]")
        total_assigned += len(entries)

    print(f"\nTotal assignments: {total_assigned}")

    changed = update_workflow_groups_yaml(definitions, assignments, dry_run=args.dry_run)
    if args.dry_run:
        print("\n[DRY RUN] No files modified.")
    elif changed:
        print(f"\nUpdated: {GROUPS_CONFIG}")
    else:
        print("\nNo changes needed.")


if __name__ == "__main__":
    main()
