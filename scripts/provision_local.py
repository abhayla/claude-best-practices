import copy
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

from scripts.bootstrap import render_template

from scripts.hub_resources import get_hub_resources, get_project_resource_names
from scripts.resource_copy import _copy_if_changed, _ensure_runtime_gitignore, _existing_pattern_names, _provision_dependency_closure, _resource_copy_units, _workflow_entry_skills
from scripts.sync_manifest import build_sync_classification, load_sync_manifest, save_sync_manifest, update_improved_to_local, update_manifest_after_sync


def apply_to_local(
    hub_root: Path,
    target_dir: Path,
    gaps: dict[str, list[dict]],
    tier: str = "must-have",
    select_workflows: Optional[set[str]] = None,
) -> list[str]:
    """Copy recommended resources from hub to a local project directory.

    Only copies resources at or above the specified tier.
    Idempotent: files already matching the hub content are skipped.

    select_workflows: if not None, provision ONLY the named workflow ORCHESTRATOR
    skills (a subset) and their transitive closures — other workflow orchestrator
    skills are skipped. Shared resources still travel (they are in a selected
    workflow's closure). Standalone patterns that are independently must-have
    still provision on their own merit (they are not "workflows"); only patterns
    reachable EXCLUSIVELY via an unselected workflow's closure (e.g. nice-to-have
    workers) are withheld. Non-workflow base patterns always provision.
    """
    copied = []
    claude_src = hub_root / "core" / ".claude"

    tiers_to_apply = ["must-have"]
    if tier == "nice-to-have":
        tiers_to_apply.append("nice-to-have")

    all_workflows = _workflow_entry_skills(hub_root) if select_workflows is not None else set()

    provisioned_names = []
    for t in tiers_to_apply:
        for item in gaps.get(t, []):
            name = item["name"]
            rtype = item["type"]
            # Selective mode: skip workflow entry-skills the user did not select.
            if select_workflows is not None and name in all_workflows and name not in select_workflows:
                continue
            units = _resource_copy_units(claude_src, target_dir, name, rtype)
            if not units:
                print(f"  WARNING: hub {rtype} '{name}' not found in {claude_src}")
                continue
            provisioned_names.append(name)
            for src, dst, label in units:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if _copy_if_changed(src, dst):
                    copied.append(label)

    # Pull in each provisioned pattern's transitive registry-`dependencies`
    # closure, so a skill's required workers/sub-skills travel with it even when
    # they are tiered nice-to-have. Without this, e.g. /development-loop ships
    # without plan-executor-agent and cannot run. Seed with both newly-copied AND
    # already-present patterns so re-provision/update also completes the closure.
    existing = _existing_pattern_names(target_dir)
    if select_workflows is not None:
        # Respect selection on re-provision: don't re-seed closures of unselected workflows.
        existing = {n for n in existing if n not in all_workflows or n in select_workflows}
    closure_seed = sorted(set(provisioned_names) | existing)
    copied.extend(_provision_dependency_closure(hub_root, target_dir, closure_seed))

    # Ensure ephemeral workflow runtime dirs are gitignored in the target project.
    _ensure_runtime_gitignore(target_dir)

    return copied


PROVISION_START_MARKER = "<!-- hub:best-practices:start -->"


PROVISION_END_MARKER = "<!-- hub:best-practices:end -->"


def get_rule_descriptions(hub_root: Path, rule_names: list[str]) -> dict[str, str]:
    """Parse YAML frontmatter description field from rule files.

    Falls back to first # heading if description is missing.
    """
    descriptions = {}
    rules_dir = hub_root / "core" / ".claude" / "rules"

    for name in rule_names:
        rule_file = rules_dir / f"{name}.md"
        if not rule_file.exists():
            continue

        content = rule_file.read_text(encoding="utf-8", errors="ignore")
        desc = None

        # Try YAML frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                frontmatter = content[3:end]
                try:
                    meta = yaml.safe_load(frontmatter)
                    if isinstance(meta, dict):
                        desc = meta.get("description")
                except yaml.YAMLError:
                    pass

        # Fallback: first # heading
        if not desc:
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("# "):
                    desc = line[2:].strip()
                    break

        if desc:
            descriptions[name] = desc

    return descriptions


def generate_hub_practices_section(
    hub_root: Path, rules_present: list[str],
    project_names: dict[str, set[str]] | None = None,
) -> str:
    """Build the hub best-practices section for CLAUDE.md.

    Intentionally compact — the previous version enumerated every rule in a
    large table, which cost ~4k tokens per session at 50+ rules. Path-scoped
    rules auto-load via `paths:` when matching files are opened; the table
    added zero enforcement value. Discovery for planning conversations is
    served by `ls .claude/rules/` or grep, not by in-file enumeration.

    Contents: protected-section header, Bug Fixing pointer, a one-line
    description of how rules are activated, and the `.claude/` inventory
    count. Length is bounded regardless of rule count.
    """
    lines = []
    lines.append(PROVISION_START_MARKER)
    lines.append("")
    lines.append("<!-- PROTECTED SECTION — managed by claude-best-practices hub. -->")
    lines.append("<!-- Do NOT condense, rewrite, reorganize, or remove.          -->")
    lines.append("<!-- Any /init or optimization request must SKIP this section.  -->")
    lines.append("")
    lines.append("## Rules for Claude")
    lines.append("")
    lines.append(
        "1. **Bug Fixing**: Use `/fix-loop` or `/fix-github-issue`. "
        "Start by writing a test that reproduces the bug, "
        "then fix and prove with a passing test."
    )
    lines.append(
        "2. **Rules**: Path-scoped rules live in `.claude/rules/` and "
        "auto-load via `paths:` frontmatter when matching files are opened. "
        "Browse with `ls .claude/rules/` — enumerating each rule here would "
        "cost ~4k tokens per session for zero enforcement benefit."
    )
    lines.append("")
    lines.append("## Claude Code Configuration")
    lines.append("")
    if project_names:
        n_skills = len(project_names.get("skill", set()))
        n_agents = len(project_names.get("agent", set()))
        n_rules = len(project_names.get("rule", set()))
        lines.append(f"The `.claude/` directory contains {n_skills} skills, {n_agents} agents, and {n_rules} rules for Claude Code.")
    else:
        lines.append("The `.claude/` directory contains skills, agents, and rules for Claude Code.")
    lines.append("")
    lines.append(PROVISION_END_MARKER)
    return "\n".join(lines)


def reconcile_claude_md_rules(target_dir: Path) -> list[str]:
    """Verify CLAUDE.md rules table matches actual files on disk.

    Returns a list of warning strings. Empty list means everything is consistent.
    """
    warnings = []
    claude_md = target_dir / "CLAUDE.md"
    rules_dir = target_dir / ".claude" / "rules"

    if not claude_md.exists():
        return warnings

    content = claude_md.read_text(encoding="utf-8")

    # Extract rule names referenced in the Rules Reference table
    # Pattern matches: | `rules/something.md` | ... |
    referenced_rules = set()
    for match in re.findall(r"\|\s*`rules/([^`]+)\.md`\s*\|", content):
        referenced_rules.add(match)

    # Get actual rule files on disk
    rules_on_disk = set()
    if rules_dir.exists():
        for f in rules_dir.glob("*.md"):
            if f.name != "README.md":
                rules_on_disk.add(f.stem)

    # Check for dangling references (in CLAUDE.md but not on disk)
    for name in sorted(referenced_rules - rules_on_disk):
        warnings.append(f"CLAUDE.md references rules/{name}.md but file does not exist")

    # Check for unreferenced rules (on disk but not in CLAUDE.md)
    for name in sorted(rules_on_disk - referenced_rules):
        warnings.append(f"rules/{name}.md exists on disk but is not listed in CLAUDE.md")

    return warnings


def provision_claude_md(
    hub_root: Path,
    target_dir: Path,
    stacks: list[str],
    rules_present: list[str],
    project_names: dict[str, set[str]] | None = None,
) -> str:
    """Provision CLAUDE.md in the target directory.

    Three cases:
    1. No CLAUDE.md exists → create from template
    2. CLAUDE.md exists with markers → replace between markers
    3. CLAUDE.md exists without markers → append section with markers
    """
    claude_md = target_dir / "CLAUDE.md"
    hub_section = generate_hub_practices_section(hub_root, rules_present, project_names)

    if not claude_md.exists():
        # Case 1: Create from template
        template_path = hub_root / "core" / ".claude" / "CLAUDE.md.template"
        if template_path.exists():
            from datetime import datetime, timezone
            template = template_path.read_text(encoding="utf-8")
            rendered = render_template(template, {
                "PROJECT_NAME": target_dir.name,
                "PROJECT_DESCRIPTION": "A new project",
                "PLATFORM": ", ".join(stacks) if stacks else "general",
                "BUILD_TOOLS": "See stack documentation",
                "DEVELOPMENT_COMMANDS": "# Add your commands here",
                "HUB_REPO": "abhayla/claude-best-practices",
                "SELECTED_STACKS": ", ".join(stacks) if stacks else "none",
                "LAST_SYNC_TIMESTAMP": datetime.now(timezone.utc).isoformat(),
            })
            # Replace hardcoded hub section with dynamic one
            start_idx = rendered.find(PROVISION_START_MARKER)
            end_idx = rendered.find(PROVISION_END_MARKER)
            if start_idx != -1 and end_idx != -1:
                before = rendered[:start_idx]
                after = rendered[end_idx + len(PROVISION_END_MARKER):]
                rendered = before + hub_section + after
            claude_md.write_text(rendered, encoding="utf-8")
            return "created"
        else:
            claude_md.write_text(f"# CLAUDE.md\n\n{hub_section}\n", encoding="utf-8")
            return "created"

    # File exists — read it
    content = claude_md.read_text(encoding="utf-8")

    # Safety net: write a rolling backup of the prior content before we
    # modify CLAUDE.md, so users can recover if the regenerated hub section
    # drops something they cared about. Single `.backup` file is overwritten
    # on each provision — if durable history is needed, that's git's job.
    (claude_md.parent / "CLAUDE.md.backup").write_text(content, encoding="utf-8")

    start_idx = content.find(PROVISION_START_MARKER)
    end_idx = content.find(PROVISION_END_MARKER)

    if start_idx != -1 and end_idx != -1:
        # Case 2: Both markers found → replace between them
        before = content[:start_idx]
        after = content[end_idx + len(PROVISION_END_MARKER):]
        new_content = before + hub_section + after
        claude_md.write_text(new_content, encoding="utf-8")
        return "replaced"

    # Case 3: No markers (or start without end) → append
    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + hub_section + "\n"
    claude_md.write_text(content, encoding="utf-8")
    return "appended"


def provision_claude_local_md(hub_root: Path, target_dir: Path) -> str:
    """Copy CLAUDE.local.md template if missing, skip if exists."""
    local_md = target_dir / "CLAUDE.local.md"
    if local_md.exists():
        return "skipped"

    template_path = hub_root / "core" / ".claude" / "CLAUDE.local.md.template"
    if template_path.exists():
        shutil.copy2(template_path, local_md)
        return "created"

    return "no-template"


def deep_merge_settings(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base. Base wins at leaf values. Lists are deduplicated union."""
    result = copy.deepcopy(base)

    for key, overlay_val in overlay.items():
        if key not in result:
            result[key] = copy.deepcopy(overlay_val)
        elif isinstance(result[key], dict) and isinstance(overlay_val, dict):
            result[key] = deep_merge_settings(result[key], overlay_val)
        elif isinstance(result[key], list) and isinstance(overlay_val, list):
            # Deduplicated union, preserving order (base items first)
            seen = set()
            merged = []
            for item in result[key] + overlay_val:
                key_repr = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                if key_repr not in seen:
                    seen.add(key_repr)
                    merged.append(item)
            result[key] = merged
        # else: base wins at leaves (do nothing)

    return result


def referenced_hook_basenames(settings: dict) -> set[str]:
    """Every `.claude/hooks/<name>.(sh|ps1)` file basename a settings dict wires.

    Walks all hook command strings across every event so callers can reconcile
    what is WIRED against what is actually delivered on disk.
    """
    names: set[str] = set()
    for blocks in settings.get("hooks", {}).values():
        for block in blocks:
            for hook in block.get("hooks", []):
                for m in re.finditer(
                    r"\.claude/hooks/([A-Za-z0-9._-]+\.(?:sh|ps1))",
                    hook.get("command", ""),
                ):
                    names.add(m.group(1))
    return names


def _deliver_referenced_hooks(hub_root: Path, target_dir: Path, settings: dict) -> list[str]:
    """Copy any hook file the settings WIRES but the target is MISSING.

    Closes the root-cause gap where settings.json merge wired a governance hook
    (e.g. ba-usecase-discovery-reminder.sh) without the file ever being copied,
    leaving a dangling reference that fails at runtime. Source of truth for
    distributable hooks is core/.claude/hooks/; target-only hooks are left
    untouched, and a hook absent from both is skipped (the consistency test
    guards the templates so that case cannot ship).
    """
    src_hooks = hub_root / "core" / ".claude" / "hooks"
    dst_hooks = target_dir / ".claude" / "hooks"
    delivered: list[str] = []
    for name in sorted(referenced_hook_basenames(settings)):
        dst = dst_hooks / name
        src = src_hooks / name
        if dst.exists() or not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        delivered.append(name)
    return delivered


def provision_settings_json(hub_root: Path, target_dir: Path) -> str:
    """Provision .claude/settings.json by merging hub defaults with existing.

    After writing, delivers every hook the resulting settings WIRES so the
    target can never reference a hook whose file was not copied.
    """
    hub_settings_path = hub_root / "core" / ".claude" / "settings.json"
    target_settings_path = target_dir / ".claude" / "settings.json"

    if not hub_settings_path.exists():
        return "no-hub-settings"

    hub_settings = json.loads(hub_settings_path.read_text(encoding="utf-8"))

    if target_settings_path.exists():
        existing = json.loads(target_settings_path.read_text(encoding="utf-8"))
        merged = deep_merge_settings(existing, hub_settings)
        target_settings_path.write_text(
            json.dumps(merged, indent=2) + "\n", encoding="utf-8"
        )
        _deliver_referenced_hooks(hub_root, target_dir, merged)
        return "merged"

    target_settings_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(hub_settings_path, target_settings_path)
    _deliver_referenced_hooks(hub_root, target_dir, hub_settings)
    return "created"


def _resolve_conflict_mode(on_conflict: str) -> str:
    """Resolve the `auto` mode based on TTY state. Both stdin and stdout must
    be TTYs for `auto` to resolve to `interactive`; if either is redirected
    the caller is programmatic and we fall back to `skip` to avoid EOFError
    on the input() prompt.

    Windows-specific: pseudo-terminals inside subprocesses often report
    sys.stdin.isatty()=True even when the caller redirected stdout, so
    checking stdin alone is insufficient. Live /synthesize-project runs
    crashed with EOFError on input() before this was tightened.
    """
    if on_conflict != "auto":
        return on_conflict
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()
    return "interactive" if is_interactive else "skip"


def provision_to_local(
    hub_root: Path,
    target_dir: Path,
    gaps: dict[str, list[dict]],
    stacks: list[str],
    tier: str = "must-have",
    on_conflict: str = "auto",
    select_workflows: Optional[set[str]] = None,
) -> dict:
    """Orchestrate full provisioning to a local directory.

    Copies missing resources, auto-updates stale hub patterns (hub-only changes),
    skips project-customized patterns, and reports conflicts.
    Provisions CLAUDE.md, CLAUDE.local.md, and settings.json.

    on_conflict controls how provisioning handles files that diverged in BOTH
    the hub and the project since last sync:
      - "auto" (default): interactive prompt if stdin is a TTY; silently skip
        if not (keeps CI and non-interactive automation from hanging)
      - "skip": always keep project versions, never prompt
      - "overwrite": always overwrite with hub versions, never prompt
      - "error": raise RuntimeError on any conflict (strict CI mode)
      - "interactive": force interactive prompt even without a TTY (will hang
        if stdin is closed — use only when you know a human is attached)
    Returns a summary dict.
    """
    # Step 1: Copy missing resources
    copied = apply_to_local(hub_root, target_dir, gaps, tier, select_workflows=select_workflows)

    # Step 1b: Copy config files whose associated skills are in the project,
    # even if the config itself is in a lower tier. Config files are runtime
    # dependencies — if the skill is present, the config must be too.
    CONFIG_SKILL_MAP = {
        "e2e-pipeline": "e2e-visual-run",
    }
    project_claude_dir = target_dir / ".claude"
    for config_name, skill_name in CONFIG_SKILL_MAP.items():
        skill_present = (project_claude_dir / "skills" / skill_name / "SKILL.md").exists()
        config_present = any(
            (project_claude_dir / "config" / f"{config_name}{ext}").exists()
            for ext in (".yml", ".yaml", ".json")
        )
        if skill_present and not config_present:
            claude_src = hub_root / "core" / ".claude"
            for ext in (".yml", ".yaml", ".json"):
                src = claude_src / "config" / f"{config_name}{ext}"
                if src.exists():
                    dst = project_claude_dir / "config" / src.name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/config/{src.name}")
                    print(f"  Copied runtime config: .claude/config/{src.name} (required by {skill_name})")
                    break

    # Step 2: Sync existing resources using 3-way manifest comparison
    manifest = load_sync_manifest(target_dir)
    hub_resources = get_hub_resources(hub_root)
    project_names = get_project_resource_names(target_dir / ".claude")

    sync_class = build_sync_classification(
        hub_root, target_dir, hub_resources, project_names, manifest,
    )

    # Auto-update hub-only and no-manifest items
    auto_update_items = sync_class["hub-only"] + sync_class["no-manifest"]
    auto_updated = update_improved_to_local(hub_root, target_dir, auto_update_items)

    # Report sync classification
    if auto_updated:
        print(f"  Auto-updated {len(auto_updated)} stale patterns")
    if sync_class["project-only"]:
        print(f"  Skipped {len(sync_class['project-only'])} project-customized patterns")
    conflict_overwritten = []
    if sync_class["conflict"]:
        n = len(sync_class["conflict"])
        print(f"\n  CONFLICTS: {n} pattern(s) changed in both hub and project:")

        # Show summary with file paths
        for i, item in enumerate(sync_class["conflict"], 1):
            print(f"    {i}. {item['name']} ({item['type']}) — {item['rel_path']}")

        # Resolve `auto` mode. Both stdin AND stdout must be TTYs to count as
        # interactive — if either is redirected, the caller is programmatic
        # (e.g. `recommend.py --json > out.json`, /synthesize-project
        # subprocess). Windows pseudo-terminals report stdin isatty=True
        # inside subprocesses even when the caller redirected stdout, so
        # checking stdin alone is insufficient.
        effective_mode = _resolve_conflict_mode(on_conflict)
        if on_conflict == "auto" and effective_mode == "skip":
            print(
                f"  -> on-conflict=auto with no interactive terminal: keeping "
                f"all {n} project versions (use --on-conflict=overwrite to flip)"
            )

        if effective_mode == "error":
            raise RuntimeError(
                f"{n} conflict(s) detected and on_conflict=error. "
                f"First conflict: {sync_class['conflict'][0]['name']}"
            )
        elif effective_mode == "overwrite":
            overwritten = update_improved_to_local(hub_root, target_dir, sync_class["conflict"])
            conflict_overwritten.extend(overwritten)
            print(f"  -> on-conflict=overwrite: replaced all {n} project versions with hub versions")
        elif effective_mode == "skip":
            print(f"  -> on-conflict=skip: kept all {n} project versions")
        elif effective_mode == "interactive":
            # Offer batch options first
            print(f"\n  Batch options: [A]ll overwrite / [S]kip all / [1] review one-by-one")
            batch_choice = input("  Choice: ").strip().lower()

            if batch_choice in ("a", "all", "all overwrite"):
                overwritten = update_improved_to_local(hub_root, target_dir, sync_class["conflict"])
                conflict_overwritten.extend(overwritten)
                print(f"  -> Overwritten all {n} conflicts with hub versions")
            elif batch_choice in ("s", "skip", "skip all"):
                print(f"  -> Kept all {n} project versions")
            else:
                # One-by-one review
                for item in sync_class["conflict"]:
                    print(f"\n    {item['name']} ({item['type']})")
                    print(f"      File: {item['rel_path']}")
                    print(f"      Hub hash:     {item['hub_hash'][:12]}...")
                    print(f"      Project hash: {item['project_hash'][:12]}...")
                    while True:
                        choice = input("      [o]verwrite / [s]kip? ").strip().lower()
                        if choice in ("o", "overwrite", "y", "yes"):
                            overwritten = update_improved_to_local(hub_root, target_dir, [item])
                            conflict_overwritten.extend(overwritten)
                            print(f"      -> Overwritten with hub version")
                            break
                        elif choice in ("s", "skip", "n", "no"):
                            print(f"      -> Kept project version")
                            break
                        else:
                            print("      Please enter 'o' (overwrite) or 's' (skip)")
        else:
            raise ValueError(
                f"Invalid on_conflict={on_conflict!r}. "
                f"Valid: auto, skip, overwrite, error, interactive"
            )

    # Update manifest with all synced files (missing copies + auto-updates + conflict overwrites)
    all_synced = copied + auto_updated + conflict_overwritten
    manifest = update_manifest_after_sync(manifest, all_synced, hub_root)

    # Also record up-to-date and project-only files in manifest (they're already synced)
    for item in sync_class["up-to-date"] + sync_class["project-only"]:
        rel = item["rel_path"]
        if rel not in manifest["files"]:
            manifest["files"][rel] = {
                "hub_hash": item["hub_hash"],
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }

    save_sync_manifest(target_dir, manifest)

    # Refresh project names after updates
    project_names = get_project_resource_names(target_dir / ".claude")
    rules_present = sorted(project_names.get("rule", set()))

    # Step 3: Provision CLAUDE.md
    claude_md_status = provision_claude_md(hub_root, target_dir, stacks, rules_present, project_names)

    # Step 4: Reconcile CLAUDE.md rules references against disk
    reconciliation_warnings = reconcile_claude_md_rules(target_dir)
    for w in reconciliation_warnings:
        print(f"  WARNING: {w}")

    # Step 5: Provision CLAUDE.local.md
    claude_local_status = provision_claude_local_md(hub_root, target_dir)

    # Step 6: Provision settings.json
    settings_status = provision_settings_json(hub_root, target_dir)

    return {
        "copied_files": copied,
        "auto_updated": auto_updated,
        "sync_classification": {
            k: len(v) for k, v in sync_class.items()
        },
        "conflicts": [
            {"name": i["name"], "type": i["type"]} for i in sync_class["conflict"]
        ],
        "conflict_overwritten": conflict_overwritten,
        "claude_md": claude_md_status,
        "claude_local_md": claude_local_status,
        "settings_json": settings_status,
        "reconciliation_warnings": reconciliation_warnings,
    }


def _copy_resources_for_tier(
    hub_root: Path,
    target_dir: Path,
    items: list[dict],
) -> list[str]:
    """Copy specific hub resources to a target directory. Returns list of copied file paths."""
    copied = []
    claude_src = hub_root / "core" / ".claude"

    for item in items:
        name = item["name"]
        rtype = item["type"]

        if rtype == "skill":
            src = claude_src / "skills" / name
            dst = target_dir / ".claude" / "skills" / name
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                for f in src.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(src)
                        dest_file = dst / rel
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dest_file)
                        copied.append(str(Path(".claude/skills") / name / rel))
        elif rtype == "agent":
            src = claude_src / "agents" / f"{name}.md"
            dst = target_dir / ".claude" / "agents" / f"{name}.md"
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/agents/{name}.md")
        elif rtype == "rule":
            src = claude_src / "rules" / f"{name}.md"
            dst = target_dir / ".claude" / "rules" / f"{name}.md"
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/rules/{name}.md")
        elif rtype == "hook":
            src = claude_src / "hooks" / f"{name}.sh"
            dst = target_dir / ".claude" / "hooks" / f"{name}.sh"
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/hooks/{name}.sh")
        elif rtype == "config":
            # Config files can be .yml, .yaml, or .json
            src = None
            for ext in (".yml", ".yaml", ".json"):
                candidate = claude_src / "config" / f"{name}{ext}"
                if candidate.exists():
                    src = candidate
                    break
            if src:
                dst = target_dir / ".claude" / "config" / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/config/{src.name}")

    return copied
