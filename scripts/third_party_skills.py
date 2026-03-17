"""Third-party agent skills detection and recommendation.

The hub facilitates discovery of third-party skills by matching project
dependencies against a curated registry. It recommends install commands
and optionally runs them via npx.

Usage (standalone):
    PYTHONPATH=. python scripts/third_party_skills.py --local /path/to/project

Typically called from recommend.py during provisioning.
"""

import fnmatch
import shutil
import subprocess
from pathlib import Path

import yaml


def load_registry(hub_root: Path) -> list[dict]:
    """Load and validate config/third-party-skills.yml.

    Returns list of skill entries. Returns empty list if file is missing or invalid.
    """
    config_path = hub_root / "config" / "third-party-skills.yml"
    if not config_path.exists():
        return []

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return []

    if not isinstance(data, dict):
        return []

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return []

    return skills


def resolve_skills(
    deps: dict[str, list[str]],
    project_dir: Path | None,
    hub_root: Path,
) -> list[dict]:
    """Match detected dependencies (and file signals) against the third-party registry.

    Args:
        deps: Dependencies grouped by ecosystem (e.g., {"npm": [...], "pip": [...]}).
        project_dir: Local project directory (for file_signals matching). None for remote repos.
        hub_root: Hub repository root (to find config/third-party-skills.yml).

    Returns list of matched skill entries, each augmented with a "match_reason" field.
    """
    registry = load_registry(hub_root)
    if not registry:
        return []

    # Flatten all dep names, and also build ecosystem-specific sets
    all_deps: set[str] = set()
    deps_by_ecosystem: dict[str, set[str]] = {}
    for ecosystem, dep_list in deps.items():
        lowered = {d.lower() for d in dep_list}
        deps_by_ecosystem[ecosystem] = lowered
        all_deps.update(lowered)

    matched = []
    seen = set()  # track repo+skill combos to prevent duplicates

    for entry in registry:
        repo = entry.get("repo", "")
        skill = entry.get("skill", "")
        key = f"{repo}:{skill}"
        if key in seen:
            continue

        match_reason = _match_entry(entry, all_deps, deps_by_ecosystem, project_dir)
        if match_reason:
            seen.add(key)
            result = dict(entry)
            result["match_reason"] = match_reason
            matched.append(result)

    return matched


def _match_entry(
    entry: dict,
    all_deps: set[str],
    deps_by_ecosystem: dict[str, set[str]],
    project_dir: Path | None,
) -> str | None:
    """Check if a registry entry matches the project. Returns match reason or None."""
    # Check dependency matching
    entry_deps = entry.get("dependencies", [])
    ecosystems_filter = entry.get("ecosystems", [])

    if entry_deps:
        if ecosystems_filter:
            # Only check deps within the specified ecosystems
            filtered_deps: set[str] = set()
            for eco in ecosystems_filter:
                filtered_deps.update(deps_by_ecosystem.get(eco, set()))
            for dep in entry_deps:
                if dep.lower() in filtered_deps:
                    eco_label = ", ".join(ecosystems_filter)
                    return f"{dep} ({eco_label})"
        else:
            # Check across all ecosystems
            for dep in entry_deps:
                if dep.lower() in all_deps:
                    # Find which ecosystem it came from
                    for eco, eco_deps in deps_by_ecosystem.items():
                        if dep.lower() in eco_deps:
                            return f"{dep} ({eco})"
                    return dep

    # Check file signal matching
    file_signals = entry.get("file_signals", [])
    if file_signals and project_dir and project_dir.is_dir():
        for pattern in file_signals:
            if _glob_matches(project_dir, pattern):
                return f"{pattern} files"

    return None


def _glob_matches(project_dir: Path, pattern: str) -> bool:
    """Check if any file in project_dir matches the glob pattern."""
    # Use pathlib glob for ** patterns
    if "**" in pattern:
        return any(True for _ in project_dir.glob(pattern))
    else:
        # Simple fnmatch against immediate children
        for child in project_dir.iterdir():
            if fnmatch.fnmatch(child.name, pattern):
                return True
    return False


def _build_install_command(entry: dict) -> str:
    """Build the npx skills add command for a registry entry."""
    repo = entry.get("repo", "")
    skill = entry.get("skill", "")
    if skill:
        return f"npx skills add {repo} --skill {skill}"
    return f"npx skills add {repo}"


def format_recommendations(matched: list[dict]) -> str:
    """Format matched third-party skills as a readable report section."""
    if not matched:
        return ""

    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  RECOMMENDED THIRD-PARTY SKILLS")
    lines.append("=" * 60)
    lines.append("")

    # Table header
    lines.append(f"  {'Skill':<30s} {'Matched On':<25s} Install Command")
    lines.append(f"  {'-----':<30s} {'----------':<25s} ---------------")

    for entry in matched:
        skill_name = entry.get("skill", entry.get("repo", "").split("/")[-1])
        reason = entry.get("match_reason", "")
        cmd = _build_install_command(entry)
        lines.append(f"  {skill_name:<30s} {reason:<25s} {cmd}")

    lines.append("")

    # Prerequisites
    prereqs = set()
    for entry in matched:
        p = entry.get("prerequisites", "")
        if p:
            prereqs.add(p)
    if prereqs:
        lines.append(f"  Prerequisites: {', '.join(sorted(prereqs))}")

    lines.append("  These skills are maintained by their respective authors.")
    lines.append("")

    # URLs
    urls = []
    for entry in matched:
        url = entry.get("url", "")
        if url and url not in urls:
            urls.append(url)
    if urls:
        lines.append("  Docs:")
        for url in urls:
            lines.append(f"    {url}")
        lines.append("")

    # Manual install commands
    lines.append("  To install manually:")
    lines.append("    cd /path/to/your/project")
    for entry in matched:
        cmd = _build_install_command(entry)
        lines.append(f"    {cmd}")
    lines.append("")

    return "\n".join(lines)


def check_npx_available() -> bool:
    """Check if npx is available on PATH."""
    return shutil.which("npx") is not None


def try_install(
    target_dir: Path,
    matched: list[dict],
    dry_run: bool = False,
) -> dict[str, str]:
    """Attempt to install matched third-party skills via npx.

    Returns dict mapping "repo:skill" to status string.
    """
    if not matched:
        return {}

    results = {}

    if not check_npx_available():
        for entry in matched:
            key = f"{entry.get('repo', '')}:{entry.get('skill', '')}"
            results[key] = "skipped (npx not available)"
        return results

    for entry in matched:
        repo = entry.get("repo", "")
        skill = entry.get("skill", "")
        key = f"{repo}:{skill}"

        if dry_run:
            results[key] = "skipped (dry run)"
            continue

        cmd = ["npx", "skills", "add", repo]
        if skill:
            cmd.extend(["--skill", skill])
        cmd.append("-y")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                results[key] = "installed"
            else:
                stderr = result.stderr.strip()[:200] if result.stderr else "unknown error"
                results[key] = f"failed ({stderr})"
        except subprocess.TimeoutExpired:
            results[key] = "failed (timeout)"
        except OSError as e:
            results[key] = f"failed ({e})"

    return results


def format_install_results(results: dict[str, str]) -> str:
    """Format install results as a readable summary."""
    if not results:
        return ""

    lines = ["", "  Third-party skill install results:"]
    for key, status in results.items():
        lines.append(f"    {key:<50s} {status}")
    lines.append("")
    return "\n".join(lines)


def validate_registry(hub_root: Path) -> list[str]:
    """Validate config/third-party-skills.yml. Returns list of errors."""
    errors = []
    config_path = hub_root / "config" / "third-party-skills.yml"

    if not config_path.exists():
        return []  # File is optional

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"third-party-skills.yml: Invalid YAML: {e}"]

    if not isinstance(data, dict):
        return ["third-party-skills.yml: Root must be a YAML mapping"]

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return ["third-party-skills.yml: 'skills' must be a list"]

    known_ecosystems = {"npm", "pip", "gradle", "pub", "cargo", "gem", "go"}
    seen_keys = set()

    for i, entry in enumerate(skills):
        prefix = f"third-party-skills.yml[{i}]"

        if not isinstance(entry, dict):
            errors.append(f"{prefix}: Entry must be a mapping")
            continue

        # Required: repo
        repo = entry.get("repo")
        if not repo or not isinstance(repo, str):
            errors.append(f"{prefix}: Missing or invalid 'repo' field")
            continue

        # Required: description
        if not entry.get("description"):
            errors.append(f"{prefix} ({repo}): Missing 'description' field")

        # At least one trigger mechanism
        deps = entry.get("dependencies", [])
        file_signals = entry.get("file_signals", [])
        if not deps and not file_signals:
            errors.append(
                f"{prefix} ({repo}): Must have non-empty 'dependencies' or 'file_signals'"
            )

        # dependencies must be a list
        if not isinstance(deps, list):
            errors.append(f"{prefix} ({repo}): 'dependencies' must be a list")

        # file_signals must be a list
        if file_signals and not isinstance(file_signals, list):
            errors.append(f"{prefix} ({repo}): 'file_signals' must be a list")

        # ecosystems must be from known set
        ecosystems = entry.get("ecosystems", [])
        if ecosystems:
            if not isinstance(ecosystems, list):
                errors.append(f"{prefix} ({repo}): 'ecosystems' must be a list")
            else:
                for eco in ecosystems:
                    if eco not in known_ecosystems:
                        errors.append(
                            f"{prefix} ({repo}): Unknown ecosystem '{eco}'. "
                            f"Known: {sorted(known_ecosystems)}"
                        )

        # No duplicate repo+skill combos
        skill = entry.get("skill", "")
        key = f"{repo}:{skill}"
        if key in seen_keys:
            errors.append(f"{prefix} ({repo}): Duplicate entry for repo '{repo}' skill '{skill}'")
        seen_keys.add(key)

    return errors
