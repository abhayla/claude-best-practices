import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from scripts.bootstrap import STACK_PREFIXES


def _resolve_hub_path(hub_root: Path, name: str, resource_type: str) -> Optional[Path]:
    """Get the file path for a hub resource."""
    claude_dir = hub_root / "core" / ".claude"
    if resource_type == "skill":
        p = claude_dir / "skills" / name / "SKILL.md"
    elif resource_type == "agent":
        p = claude_dir / "agents" / f"{name}.md"
    elif resource_type == "rule":
        p = claude_dir / "rules" / f"{name}.md"
    elif resource_type == "hook":
        p = claude_dir / "hooks" / f"{name}.sh"
    elif resource_type == "config":
        # Config files can be .yml, .yaml, or .json
        for ext in (".yml", ".yaml", ".json"):
            p = claude_dir / "config" / f"{name}{ext}"
            if p.exists():
                return p
        return None
    else:
        return None
    return p if p.exists() else None


def _resolve_project_path(claude_dir: Path, name: str, resource_type: str) -> Optional[Path]:
    """Get the file path for a project resource."""
    if resource_type == "skill":
        p = claude_dir / "skills" / name / "SKILL.md"
    elif resource_type == "agent":
        p = claude_dir / "agents" / f"{name}.md"
    elif resource_type == "rule":
        p = claude_dir / "rules" / f"{name}.md"
    elif resource_type == "hook":
        p = claude_dir / "hooks" / f"{name}.sh"
    elif resource_type == "config":
        for ext in (".yml", ".yaml", ".json"):
            p = claude_dir / "config" / f"{name}{ext}"
            if p.exists():
                return p
        return None
    else:
        return None
    return p if p.exists() else None


def _find_matching_project_name(hub_name: str, project_names: set[str]) -> Optional[str]:
    """Find the project resource name that matches a hub name (accounting for prefixes)."""
    if hub_name in project_names:
        return hub_name

    # Hub prefixed → project unprefixed
    for prefix in STACK_PREFIXES.values():
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            if stripped in project_names:
                return stripped

    # Project prefixed → hub unprefixed
    for prefix in STACK_PREFIXES.values():
        if f"{prefix}{hub_name}" in project_names:
            return f"{prefix}{hub_name}"

    # Reversed prefix
    for prefix in STACK_PREFIXES.values():
        keyword = prefix.rstrip("-")
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            for pname in project_names:
                if keyword in pname and stripped.split("-")[-1] in pname:
                    return pname

    return None


def _compute_line_overlap(hub_lines: list[str], project_lines: list[str]) -> float:
    """Compute what fraction of hub lines appear in the project content (normalized).

    Returns a float 0.0-1.0 representing how much of the hub's content is present
    in the project version.
    """
    if not hub_lines:
        return 1.0

    # Normalize lines for comparison (strip, lowercase, skip empty/comment)
    def normalize(lines):
        return {
            line.strip().lower()
            for line in lines
            if line.strip() and not line.strip().startswith("---")
        }

    hub_set = normalize(hub_lines)
    proj_set = normalize(project_lines)

    if not hub_set:
        return 1.0

    overlap = hub_set & proj_set
    return len(overlap) / len(hub_set)


def classify_divergence(
    hub_content: str,
    project_content: str,
) -> dict:
    """Classify the divergence between hub and project versions of a resource.

    Returns a dict with:
      - status: 'identical', 'hub-newer', 'project-customized', 'name-collision'
      - hub_lines: int
      - project_lines: int
      - hub_overlap: float (fraction of hub lines found in project)
      - detail: str (human-readable explanation)
    """
    hub_lines = hub_content.splitlines()
    proj_lines = project_content.splitlines()
    hub_line_count = len(hub_lines)
    proj_line_count = len(proj_lines)

    # Exact match
    if hub_content.strip() == project_content.strip():
        return {
            "status": "identical",
            "hub_lines": hub_line_count,
            "project_lines": proj_line_count,
            "hub_overlap": 1.0,
            "detail": "Content is identical",
        }

    hub_overlap = _compute_line_overlap(hub_lines, proj_lines)

    # Also check reverse: how much of project content is in hub
    proj_overlap = _compute_line_overlap(proj_lines, hub_lines)

    # High overlap in either direction — project is a customized extension of hub
    if hub_overlap >= 0.5 or proj_overlap >= 0.5:
        if proj_line_count > hub_line_count * 1.3:
            return {
                "status": "project-customized",
                "hub_lines": hub_line_count,
                "project_lines": proj_line_count,
                "hub_overlap": hub_overlap,
                "detail": (
                    f"Project extends hub ({proj_line_count} vs {hub_line_count} lines, "
                    f"{hub_overlap:.0%} hub content preserved). "
                    "Project adds project-specific customizations."
                ),
            }
        else:
            return {
                "status": "project-customized",
                "hub_lines": hub_line_count,
                "project_lines": proj_line_count,
                "hub_overlap": hub_overlap,
                "detail": (
                    f"Minor variations ({proj_line_count} vs {hub_line_count} lines, "
                    f"{hub_overlap:.0%} overlap)."
                ),
            }

    # Project is much larger (2x+) with low overlap — project heavily customized
    # the hub template. This is NOT a name collision — it's a deep rewrite.
    if proj_line_count > hub_line_count * 1.5 and hub_overlap < 0.5:
        return {
            "status": "project-customized",
            "hub_lines": hub_line_count,
            "project_lines": proj_line_count,
            "hub_overlap": hub_overlap,
            "detail": (
                f"Project heavily customized hub template "
                f"({proj_line_count} vs {hub_line_count} lines, "
                f"{hub_overlap:.0%} hub content preserved). "
                "Hub may have generic improvements worth reviewing."
            ),
        }

    # Hub is larger with low overlap — hub has content project is missing
    if hub_line_count > proj_line_count and hub_overlap < 0.5:
        return {
            "status": "hub-newer",
            "hub_lines": hub_line_count,
            "project_lines": proj_line_count,
            "hub_overlap": hub_overlap,
            "detail": (
                f"Hub has significant content the project lacks "
                f"({hub_line_count} vs {proj_line_count} lines, "
                f"only {hub_overlap:.0%} overlap). "
                "Consider updating project from hub."
            ),
        }

    # Similar size, very low overlap — true name collision (different purpose)
    if hub_overlap < 0.15 and proj_overlap < 0.15:
        size_ratio = max(proj_line_count, hub_line_count) / max(min(proj_line_count, hub_line_count), 1)
        if size_ratio < 2.0:
            return {
                "status": "name-collision",
                "hub_lines": hub_line_count,
                "project_lines": proj_line_count,
                "hub_overlap": hub_overlap,
                "detail": (
                    f"Very low content overlap ({hub_overlap:.0%}) with similar size. "
                    f"These may be different resources sharing a name "
                    f"({proj_line_count} project vs {hub_line_count} hub lines). "
                    "Review manually."
                ),
            }

    # Default: moderate divergence
    return {
        "status": "project-customized",
        "hub_lines": hub_line_count,
        "project_lines": proj_line_count,
        "hub_overlap": hub_overlap,
        "detail": (
            f"Content has diverged ({hub_overlap:.0%} overlap, "
            f"{proj_line_count} project vs {hub_line_count} hub lines). "
            "Hub may have generic improvements worth reviewing."
        ),
    }


def analyze_overlaps_local(
    hub_root: Path,
    project_dir: Path,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
) -> list[dict]:
    """Compare content of overlapping resources between hub and a local project."""
    results = []
    claude_dir = project_dir / ".claude"

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            hub_name = resource["name"]
            proj_name = _find_matching_project_name(
                hub_name, project_names.get(resource_type, set())
            )
            if proj_name is None:
                continue

            hub_path = _resolve_hub_path(hub_root, hub_name, resource_type)
            proj_path = _resolve_project_path(claude_dir, proj_name, resource_type)

            if not hub_path or not proj_path:
                continue

            try:
                hub_content = hub_path.read_text(encoding="utf-8", errors="ignore")
                proj_content = proj_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            divergence = classify_divergence(hub_content, proj_content)
            divergence["hub_name"] = hub_name
            divergence["project_name"] = proj_name
            divergence["type"] = resource_type
            results.append(divergence)

    return results


def analyze_overlaps_repo(
    hub_root: Path,
    repo: str,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
) -> list[dict]:
    """Compare content of overlapping resources between hub and a remote repo."""
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", "--depth=2", "--filter=blob:none",
                 "--sparse", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=60,
            )
            subprocess.run(
                ["git", "-C", tmpdir, "sparse-checkout", "set", ".claude/"],
                capture_output=True, text=True, check=True, timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return results

        return analyze_overlaps_local(
            hub_root, Path(tmpdir), hub_resources, project_names
        )


def format_diff_report(overlaps: list[dict]) -> str:
    """Format the content divergence analysis as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CONTENT DIVERGENCE REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Group by status
    by_status = {}
    for item in overlaps:
        status = item["status"]
        by_status.setdefault(status, []).append(item)

    # Count summary
    total = len(overlaps)
    identical = len(by_status.get("identical", []))
    lines.append(f"Total overlapping resources: {total}")
    lines.append(f"Identical: {identical}")
    lines.append("")

    # Actionable items first
    actionable_statuses = [
        ("name-collision", "NAME COLLISIONS — Different resources sharing a name"),
        ("hub-newer", "HUB HAS IMPROVEMENTS — Consider updating project"),
    ]

    for status, header in actionable_statuses:
        items = by_status.get(status, [])
        if not items:
            continue
        lines.append(f"--- {header} ({len(items)}) ---")
        for item in sorted(items, key=lambda x: x["hub_name"]):
            name_display = item["hub_name"]
            if item["hub_name"] != item["project_name"]:
                name_display = f"{item['hub_name']} (project: {item['project_name']})"
            lines.append(f"  [{item['type']:6s}] {name_display}")
            lines.append(f"           {item['detail']}")
        lines.append("")

    # Informational
    customized = by_status.get("project-customized", [])
    if customized:
        lines.append(f"--- PROJECT CUSTOMIZED — No action needed ({len(customized)}) ---")
        for item in sorted(customized, key=lambda x: x["hub_name"]):
            name_display = item["hub_name"]
            if item["hub_name"] != item["project_name"]:
                name_display = f"{item['hub_name']} (project: {item['project_name']})"
            ratio = item["project_lines"] / max(item["hub_lines"], 1)
            lines.append(
                f"  [{item['type']:6s}] {name_display} "
                f"({item['project_lines']} vs {item['hub_lines']} lines, "
                f"{item['hub_overlap']:.0%} overlap)"
            )
        lines.append("")

    identical_items = by_status.get("identical", [])
    if identical_items:
        lines.append(f"--- IDENTICAL ({len(identical_items)}) ---")
        for item in sorted(identical_items, key=lambda x: x["hub_name"]):
            lines.append(f"  [{item['type']:6s}] {item['hub_name']} ({item['hub_lines']} lines)")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_divergence_table(overlaps: list[dict]) -> str:
    """Format overlaps as a markdown table for PR body. Skips identical items."""
    non_identical = [o for o in overlaps if o["status"] != "identical"]
    if not non_identical:
        return ""

    lines = []
    lines.append("## Content Divergence")
    lines.append("")
    lines.append("| Resource | Type | Status | Overlap | Detail |")
    lines.append("|----------|------|--------|---------|--------|")
    for item in sorted(non_identical, key=lambda x: x["hub_name"]):
        name = item["hub_name"]
        if item.get("project_name") and item["project_name"] != name:
            name = f"{name} (project: {item['project_name']})"
        lines.append(
            f"| {name} | {item['type']} | {item['status']} "
            f"| {item['hub_overlap']:.0%} | {item['detail'][:80]} |"
        )

    return "\n".join(lines)
