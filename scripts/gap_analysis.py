import hashlib
from pathlib import Path
import yaml

from scripts.dependency_detection import detect_dependencies_from_dir, resolve_dep_patterns
from scripts.hub_resources import matches_stacks, name_matches_existing
from scripts.overlap_analysis import _find_matching_project_name, _resolve_project_path
from scripts.provisioning_tiers import tier_resource_with_reason


def analyze_gaps(
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    stacks: list[str],
    deps: dict[str, list[str]] | None = None,
) -> dict[str, list[dict]]:
    """Compare hub resources against project resources and tier the gaps.

    Args:
        deps: Dependency info from detect_dependencies_from_dir/repo.
            Used to auto-promote patterns matching detected dependencies.

    Returns dict with keys 'must-have', 'improved', 'nice-to-have', 'skip',
    each containing a list of {'name': str, 'type': str, 'tier': str}.
    """
    dep_promoted = resolve_dep_patterns(deps) if deps else set()
    gaps = {"must-have": [], "improved": [], "nice-to-have": [], "skip": []}

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            name = resource["name"]

            # Skip if project already has it (accounting for name variations)
            if name_matches_existing(name, project_names.get(resource_type, set())):
                continue

            # Wrong-stack check — but dep-promoted patterns override this
            if not matches_stacks(name, stacks) and not (dep_promoted and name in dep_promoted):
                gaps["skip"].append({
                    "name": name, "type": resource_type, "tier": "skip",
                    "reason": "wrong stack",
                })
                continue

            tier, reason = tier_resource_with_reason(name, resource_type, stacks, dep_promoted)
            gaps[tier].append({
                "name": name, "type": resource_type, "tier": tier,
                "reason": reason,
            })

    return gaps


def _parse_frontmatter_version(content: str) -> str | None:
    """Extract version from YAML frontmatter of a pattern file."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    try:
        meta = yaml.safe_load(content[3:end])
        if isinstance(meta, dict):
            return meta.get("version")
    except yaml.YAMLError:
        pass
    return None


def _version_gt(a: str | None, b: str | None) -> bool:
    """Return True if version a > version b (simple semver comparison)."""
    if not a or not b:
        return False
    try:
        a_parts = [int(x) for x in a.split(".")]
        b_parts = [int(x) for x in b.split(".")]
        return a_parts > b_parts
    except (ValueError, AttributeError):
        return False


def detect_improved_patterns(
    hub_root: Path,
    project_claude_dir: Path,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    registry: dict,
) -> list[dict]:
    """Detect patterns that exist in both hub and project but hub has a newer version.

    For each overlapping pattern:
    1. Compute project file hash (SHA256)
    2. Get hub hash from registry
    3. Compare versions to determine if hub has improvements

    Returns list of {"name", "type", "hub_version", "project_version", "reason"}.
    """
    improved = []

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            hub_name = resource["name"]
            proj_name = _find_matching_project_name(
                hub_name, project_names.get(resource_type, set())
            )
            if proj_name is None:
                continue

            # Resolve project file path
            proj_path = _resolve_project_path(project_claude_dir, proj_name, resource_type)
            if not proj_path:
                continue

            # Compute project file hash
            try:
                proj_content = proj_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            proj_hash = hashlib.sha256(proj_content.encode("utf-8")).hexdigest()

            # Get hub hash from registry
            reg_entry = registry.get(hub_name, {})
            hub_hash = reg_entry.get("hash")

            if hub_hash and proj_hash == hub_hash:
                continue  # Identical — skip

            # Parse versions
            proj_version = _parse_frontmatter_version(proj_content)
            hub_version = reg_entry.get("version")

            if _version_gt(hub_version, proj_version):
                improved.append({
                    "name": hub_name,
                    "type": resource_type,
                    "hub_version": hub_version,
                    "project_version": proj_version,
                    "reason": f"hub v{hub_version} > project v{proj_version}",
                })
            elif proj_version is None and hub_version:
                improved.append({
                    "name": hub_name,
                    "type": resource_type,
                    "hub_version": hub_version,
                    "project_version": None,
                    "reason": "project has no version, hub has v" + hub_version,
                })
            elif hub_hash and proj_hash != hub_hash and proj_version == hub_version:
                improved.append({
                    "name": hub_name,
                    "type": resource_type,
                    "hub_version": hub_version,
                    "project_version": proj_version,
                    "reason": f"same version ({hub_version}) but different content",
                })
            # else: project version >= hub version — project customized intentionally

    return improved


def format_report(
    gaps: dict[str, list[dict]],
    stacks: list[str],
    project_names: dict[str, set[str]],
    hub_resources: dict[str, list[dict]],
) -> str:
    """Format the gap analysis as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CLAUDE RESOURCES RECOMMENDATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    existing = sum(len(v) for v in project_names.values())
    hub_total = sum(len(v) for v in hub_resources.values())
    lines.append(f"Detected stacks: {', '.join(stacks) if stacks else 'none'}")
    lines.append(f"Project resources: {existing}")
    lines.append(f"Hub resources (eligible): {hub_total}")
    lines.append("")

    # Must-have
    must = gaps["must-have"]
    if must:
        lines.append(f"--- MUST-HAVE ({len(must)}) ---")
        for item in sorted(must, key=lambda x: (x["type"], x["name"])):
            lines.append(f"  [{item['type']:6s}] {item['name']}")
        lines.append("")

    # Improved
    improved = gaps.get("improved", [])
    if improved:
        lines.append(f"--- IMPROVED ({len(improved)}) ---")
        for item in sorted(improved, key=lambda x: (x["type"], x["name"])):
            reason = item.get("reason", "")
            suffix = f" ({reason})" if reason else ""
            lines.append(f"  [{item['type']:6s}] {item['name']}{suffix}")
        lines.append("")

    # Nice-to-have
    nice = gaps["nice-to-have"]
    if nice:
        lines.append(f"--- NICE-TO-HAVE ({len(nice)}) ---")
        for item in sorted(nice, key=lambda x: (x["type"], x["name"])):
            lines.append(f"  [{item['type']:6s}] {item['name']}")
        lines.append("")

    # Skip
    skip = gaps["skip"]
    if skip:
        lines.append(f"--- SKIP ({len(skip)}) ---")
        for item in sorted(skip, key=lambda x: (x["type"], x["name"])):
            reason = item.get("reason", "")
            suffix = f" ({reason})" if reason else ""
            lines.append(f"  [{item['type']:6s}] {item['name']}{suffix}")
        lines.append("")

    # Totals
    lines.append("=" * 60)
    lines.append(
        f"TOTAL: {len(must)} must-have, {len(improved)} improved, "
        f"{len(nice)} nice-to-have, {len(skip)} skip"
    )
    lines.append("=" * 60)

    return "\n".join(lines)
