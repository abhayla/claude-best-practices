import shutil
from pathlib import Path
import yaml

from scripts.provisioning_tiers import _load_tier_registry


def _copy_if_changed(src: Path, dest: Path) -> bool:
    """Copy src to dest only if dest is missing or has different content.

    Returns True if a copy was performed, False if dest was already in sync
    (idempotent no-op). Keeps repeated provisioning runs from churning
    unchanged files.
    """
    if dest.exists() and src.read_bytes() == dest.read_bytes():
        return False
    shutil.copy2(src, dest)
    return True


RUNTIME_IGNORE_ENTRIES = (".workflows/", "test-results/", "test-evidence/")


_RUNTIME_IGNORE_HEADER = "# Ephemeral Claude Code workflow runtime artifacts (claude-best-practices hub)"


def _ensure_runtime_gitignore(target_dir: Path) -> bool:
    """Ensure the project's .gitignore ignores ephemeral workflow runtime dirs.

    Idempotent: appends only entries not already present. Returns True if the
    file was modified.
    """
    gitignore = target_dir / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    present = {line.strip() for line in existing.splitlines()}
    missing = [e for e in RUNTIME_IGNORE_ENTRIES if e not in present]
    if not missing:
        return False
    block = ""
    if existing and not existing.endswith("\n"):
        block += "\n"
    if _RUNTIME_IGNORE_HEADER not in present:
        block += f"\n{_RUNTIME_IGNORE_HEADER}\n"
    block += "".join(f"{e}\n" for e in missing)
    gitignore.write_text(existing + block, encoding="utf-8")
    return True


def _resource_copy_units(
    claude_src: Path, target_dir: Path, name: str, rtype: str
) -> list[tuple[Path, Path, str]]:
    """Resolve a resource to its (src_file, dst_file, label) copy units.

    Returns an empty list if the hub source is missing. A skill expands to one
    unit per file in its directory; other resource types are a single file.
    """
    units: list[tuple[Path, Path, str]] = []
    if rtype == "skill":
        src = claude_src / "skills" / name
        if src.is_dir():
            for f in src.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(src)
                    units.append(
                        (f, target_dir / ".claude" / "skills" / name / rel,
                         str(Path(".claude/skills") / name / rel))
                    )
    elif rtype == "agent":
        src = claude_src / "agents" / f"{name}.md"
        if src.exists():
            units.append((src, target_dir / ".claude" / "agents" / f"{name}.md",
                          f".claude/agents/{name}.md"))
    elif rtype == "rule":
        src = claude_src / "rules" / f"{name}.md"
        if src.exists():
            units.append((src, target_dir / ".claude" / "rules" / f"{name}.md",
                          f".claude/rules/{name}.md"))
    elif rtype == "hook":
        src = claude_src / "hooks" / f"{name}.sh"
        if src.exists():
            units.append((src, target_dir / ".claude" / "hooks" / f"{name}.sh",
                          f".claude/hooks/{name}.sh"))
    elif rtype == "config":
        for ext in (".yml", ".yaml", ".json"):
            cand = claude_src / "config" / f"{name}{ext}"
            if cand.exists():
                units.append((cand, target_dir / ".claude" / "config" / cand.name,
                              f".claude/config/{cand.name}"))
                break
    return units


def _existing_pattern_names(target_dir: Path) -> set[str]:
    """Names of patterns already present in the target project's .claude/.

    Used to seed the dependency-closure walk so an already-provisioned skill that
    is missing a (nice-to-have) worker gets it filled on re-provision/update — not
    only on a clean first provision.
    """
    claude = target_dir / ".claude"
    names: set[str] = set()
    skills_dir = claude / "skills"
    if skills_dir.is_dir():
        names.update(p.name for p in skills_dir.iterdir() if (p / "SKILL.md").exists())
    for sub, suffix in (("agents", ".md"), ("rules", ".md"), ("hooks", ".sh")):
        d = claude / sub
        if d.is_dir():
            names.update(p.stem for p in d.glob(f"*{suffix}"))
    return names


def _provision_dependency_closure(
    hub_root: Path, target_dir: Path, seed_names: list[str]
) -> list[str]:
    """Copy the transitive registry-`dependencies` closure of seed_names.

    Provisioning selects patterns by tier, but a workflow skill's required
    workers/sub-skills may be tiered nice-to-have and get skipped — leaving the
    skill unable to run. This walks each provisioned pattern's declared
    `dependencies` and copies them in regardless of their own tier, so the
    closure always travels with the skill. Deprecated dependencies are skipped.
    Returns the list of copied file labels.
    """
    registry = _load_tier_registry(hub_root)
    if not registry:
        return []
    claude_src = hub_root / "core" / ".claude"
    copied: list[str] = []
    seen = set(seed_names)
    queue = list(seed_names)
    while queue:
        entry = registry.get(queue.pop())
        if not isinstance(entry, dict):
            continue
        for dep in entry.get("dependencies", []) or []:
            if dep in seen:
                continue
            seen.add(dep)
            queue.append(dep)
            dep_entry = registry.get(dep)
            if not isinstance(dep_entry, dict):
                print(f"  WARNING: dependency '{dep}' not in registry — cannot provision closure")
                continue
            if dep_entry.get("deprecated"):
                continue
            units = _resource_copy_units(claude_src, target_dir, dep, dep_entry.get("type", ""))
            if not units:
                print(f"  WARNING: dependency '{dep}' ({dep_entry.get('type')}) has no hub source files")
                continue
            for src, dst, label in units:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if _copy_if_changed(src, dst):
                    copied.append(label)
    return copied


def _workflow_entry_skills(hub_root: Path) -> set[str]:
    """Names of the workflow entry-skills, from config/workflow-contracts.yaml.

    These are the patterns a user selects among; all OTHER patterns (base rules,
    stack skills) are not workflow-scoped and always provision per stack/tier.
    """
    import yaml
    p = hub_root / "config" / "workflow-contracts.yaml"
    if not p.exists():
        return set()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {(spec or {}).get("entry_skill", wf)
            for wf, spec in (data.get("workflows") or {}).items()}
