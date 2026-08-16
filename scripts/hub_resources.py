import subprocess
import tempfile
from pathlib import Path

from scripts.bootstrap import STACK_PREFIXES


def get_hub_resources(hub_root: Path) -> dict[str, list[dict]]:
    """Get all resources from core/.claude/ organized by type."""
    claude_dir = hub_root / "core" / ".claude"
    resources = {"skill": [], "agent": [], "rule": [], "hook": [], "config": []}

    # Skills
    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                resources["skill"].append({"name": skill_dir.name, "path": skill_file})

    # Agents
    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            resources["agent"].append({"name": f.stem, "path": f})

    # Rules
    rules_dir = claude_dir / "rules"
    if rules_dir.exists():
        for f in sorted(rules_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            resources["rule"].append({"name": f.stem, "path": f})

    # Hooks
    hooks_dir = claude_dir / "hooks"
    if hooks_dir.exists():
        for f in sorted(hooks_dir.glob("*.sh")):
            resources["hook"].append({"name": f.stem, "path": f})

    # Config files
    config_dir = claude_dir / "config"
    if config_dir.exists():
        for f in sorted(config_dir.glob("*.yml")):
            resources["config"].append({"name": f.stem, "path": f})
        for f in sorted(config_dir.glob("*.yaml")):
            resources["config"].append({"name": f.stem, "path": f})
        for f in sorted(config_dir.glob("*.json")):
            resources["config"].append({"name": f.stem, "path": f})

    return resources


def get_project_resource_names(claude_dir: Path) -> dict[str, set[str]]:
    """Get names of all resources in a project's .claude/ directory."""
    names = {"skill": set(), "agent": set(), "rule": set(), "hook": set(), "config": set()}

    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        for d in skills_dir.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                names["skill"].add(d.name)

    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for f in agents_dir.glob("*.md"):
            if f.name != "README.md":
                names["agent"].add(f.stem)

    rules_dir = claude_dir / "rules"
    if rules_dir.exists():
        for f in rules_dir.glob("*.md"):
            if f.name != "README.md":
                names["rule"].add(f.stem)

    hooks_dir = claude_dir / "hooks"
    if hooks_dir.exists():
        for f in hooks_dir.glob("*.sh"):
            names["hook"].add(f.stem)

    config_dir = claude_dir / "config"
    if config_dir.exists():
        for f in config_dir.iterdir():
            if f.is_file() and f.suffix in (".yml", ".yaml", ".json"):
                names["config"].add(f.stem)

    return names


def get_project_resources_from_repo(repo: str) -> dict[str, set[str]]:
    """Get resource names from a remote repo via sparse clone."""
    names = {"skill": set(), "agent": set(), "rule": set(), "hook": set(), "config": set()}

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", "--filter=blob:none",
                 "--sparse", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=60,
            )
            subprocess.run(
                ["git", "-C", tmpdir, "sparse-checkout", "set", ".claude/"],
                capture_output=True, text=True, check=True, timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return names

        claude_dir = Path(tmpdir) / ".claude"
        return get_project_resource_names(claude_dir)


def is_stack_specific(name: str) -> bool:
    """Check if a resource name has a stack prefix."""
    all_prefixes = set(STACK_PREFIXES.values())
    return any(name.startswith(p) for p in all_prefixes)


def matches_stacks(name: str, stacks: list[str]) -> bool:
    """Check if a resource matches the selected stacks (or is universal)."""
    all_prefixes = set(STACK_PREFIXES.values())
    if not any(name.startswith(p) for p in all_prefixes):
        return True  # Universal — always matches

    allowed_prefixes = {STACK_PREFIXES[s] for s in stacks if s in STACK_PREFIXES}
    return any(name.startswith(p) for p in allowed_prefixes)


def name_matches_existing(hub_name: str, project_names: set[str]) -> bool:
    """Check if a hub resource name matches a project resource, accounting for prefix differences.

    E.g., hub 'android-adb-test' matches project 'adb-test'.
    E.g., hub 'android-run-tests' matches project 'run-android-tests'.
    """
    if hub_name in project_names:
        return True

    # Strip known prefixes and check again
    for prefix in STACK_PREFIXES.values():
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            if stripped in project_names:
                return True

    # Check if project has a prefixed version of a universal hub name
    for prefix in STACK_PREFIXES.values():
        if f"{prefix}{hub_name}" in project_names:
            return True

    # Handle reversed prefix patterns: hub 'android-run-tests' ↔ project 'run-android-tests'
    # Extract the stack keyword from hub prefix and check if project has it embedded
    for prefix in STACK_PREFIXES.values():
        keyword = prefix.rstrip("-")  # "android-" → "android"
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            # Check: project has "{stripped_part}-{keyword}-{rest}" or "{verb}-{keyword}-{noun}"
            for pname in project_names:
                if keyword in pname and stripped.split("-")[-1] in pname:
                    return True

    return False
