"""Recommend hub Claude resources for a project based on stack detection and gap analysis.

Usage:
    # Report only (remote repo)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name

    # Report only (local directory)
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project

    # Apply recommendations via PR (remote repo)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --apply

    # Apply recommendations locally (copy files)
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --apply

    # Provision project (apply + CLAUDE.md + settings.json)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --provision
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --provision

    # Use stacks from repos.yml instead of auto-detection
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --use-config

    # Compare content of overlapping resources (detect divergence)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --diff
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --diff
"""

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from scripts.bootstrap import STACK_PREFIXES, copy_claude_dir, render_template
from scripts.collate import extract_patterns_from_dir


# --- Stack Detection ---

# Maps config file patterns to stack identifiers.
# Each entry: (file_glob, content_pattern_or_None, stack_name)
STACK_DETECTORS = [
    # Android: build.gradle.kts with android plugin
    ("**/build.gradle.kts", "com.android", "android-compose"),
    ("**/build.gradle", "com.android", "android-compose"),
    # FastAPI: requirements.txt with fastapi
    ("**/requirements.txt", "fastapi", "fastapi-python"),
    ("**/pyproject.toml", "fastapi", "fastapi-python"),
    ("**/Pipfile", "fastapi", "fastapi-python"),
    # Firebase: google-services.json or firebase dependency
    ("**/google-services.json", None, "firebase-auth"),
    ("**/requirements.txt", "firebase", "firebase-auth"),
    ("**/build.gradle.kts", "firebase", "firebase-auth"),
    # AI/Gemini: google-genai or anthropic SDK
    ("**/requirements.txt", "google-genai", "ai-gemini"),
    ("**/requirements.txt", "anthropic", "ai-gemini"),
    ("**/pyproject.toml", "google-genai", "ai-gemini"),
    # React/Next.js: package.json with next
    ("**/package.json", '"next"', "react-nextjs"),
]

# Safety hooks that every project should have
MUST_HAVE_HOOKS = {"dangerous-command-blocker", "secret-scanner"}

# Universal skills that are high-value for any non-trivial project
MUST_HAVE_UNIVERSAL_SKILLS = {
    "skill-master",         # Routing — critical when skill count > 15
    "systematic-debugging",  # Root cause analysis
    "tdd",                  # Test-driven development
    "pr-standards",         # PR quality gate
    "request-code-review",  # Review-optimized PRs
    "receive-code-review",  # Act on review feedback
    "pg-query",             # PostgreSQL query assistant — must-have for any project using PostgreSQL
    "compose-ui",           # Jetpack Compose UI — must-have for Compose projects
}

# Universal skills that are nice-to-have
NICE_TO_HAVE_UNIVERSAL_SKILLS = {
    "security-audit",
    "adversarial-review",
    "branching",
    "git-worktrees",
    "brainstorm",
    "writing-plans",
    "executing-plans",
    "subagent-driven-dev",
    "batch",
    "handover",
    "supply-chain-audit",
    "learn-n-improve",
}

# Universal rules that are high-value
MUST_HAVE_RULES = {"context-management", "rule-writing-meta"}

# Universal agents that are high-value
MUST_HAVE_AGENTS = {"security-auditor"}

# Skills/resources to always skip (meta hub skills, wrong-domain)
ALWAYS_SKIP = {
    "update-practices", "contribute-practice", "writing-skills",
    "d3-viz", "obsidian", "solidity-audit", "playwright",
    "remotion-video", "web-quality", "mcp-server-builder",
    "twitter-x", "reddit", "github",
    # Cross-platform frameworks — skip unless project actually uses them
    "vue-dev", "nuxt-dev", "expo-dev", "flutter-dev", "flutter-e2e-test",
    "react-native-dev",
}

# Stack-specific skills that should be downgraded to nice-to-have
# (they match by prefix but aren't essential for most projects using that stack)
NICE_TO_HAVE_STACK_OVERRIDES = {
    "firebase-data-connect",  # PostgreSQL + GraphQL — most Firebase projects don't use this
    "xml-to-compose",         # Only needed for XML-to-Compose migration, not greenfield
}


def detect_stacks_from_dir(project_dir: Path) -> list[str]:
    """Auto-detect tech stacks from project config files."""
    detected = set()

    for glob_pattern, content_pattern, stack in STACK_DETECTORS:
        matching_files = list(project_dir.rglob(glob_pattern.replace("**/", "")))
        if not matching_files:
            continue

        if content_pattern is None:
            # File existence is enough (e.g., google-services.json)
            detected.add(stack)
            continue

        for f in matching_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if content_pattern.lower() in content.lower():
                    detected.add(stack)
                    break
            except (OSError, UnicodeDecodeError):
                continue

    return sorted(detected)


def detect_stacks_from_repo(repo: str) -> list[str]:
    """Auto-detect stacks from a remote GitHub repo using gh API."""
    detected = set()

    # Check key files via GitHub API
    checks = [
        ("android/build.gradle.kts", "com.android", "android-compose"),
        ("android/app/build.gradle.kts", "com.android", "android-compose"),
        ("build.gradle.kts", "com.android", "android-compose"),
        ("requirements.txt", "fastapi", "fastapi-python"),
        ("backend/requirements.txt", "fastapi", "fastapi-python"),
        ("android/app/google-services.json", None, "firebase-auth"),
        ("google-services.json", None, "firebase-auth"),
        ("requirements.txt", "firebase", "firebase-auth"),
        ("backend/requirements.txt", "firebase", "firebase-auth"),
        ("requirements.txt", "google-genai", "ai-gemini"),
        ("backend/requirements.txt", "google-genai", "ai-gemini"),
        ("requirements.txt", "anthropic", "ai-gemini"),
        ("backend/requirements.txt", "anthropic", "ai-gemini"),
        ("package.json", '"next"', "react-nextjs"),
    ]

    for file_path, content_pattern, stack in checks:
        if stack in detected:
            continue
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                continue

            if content_pattern is None:
                # File existence is enough
                detected.add(stack)
                continue

            # Content is base64 encoded from GitHub API
            import base64
            content = base64.b64decode(result.stdout.strip()).decode("utf-8", errors="ignore")
            if content_pattern.lower() in content.lower():
                detected.add(stack)
        except Exception:
            continue

    return sorted(detected)


def get_stacks_from_config(repo: str, config_path: Path) -> Optional[list[str]]:
    """Get stacks from repos.yml config if the repo is registered."""
    if not config_path.exists():
        return None
    with open(config_path) as f:
        data = yaml.safe_load(f)
    for entry in data.get("repos", []):
        if entry.get("repo") == repo:
            return entry.get("stacks", [])
    return None


# --- Resource Inventory ---


def get_hub_resources(hub_root: Path) -> dict[str, list[dict]]:
    """Get all resources from core/.claude/ organized by type."""
    claude_dir = hub_root / "core" / ".claude"
    resources = {"skill": [], "agent": [], "rule": [], "hook": []}

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

    return resources


def get_project_resource_names(claude_dir: Path) -> dict[str, set[str]]:
    """Get names of all resources in a project's .claude/ directory."""
    names = {"skill": set(), "agent": set(), "rule": set(), "hook": set()}

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

    return names


def get_project_resources_from_repo(repo: str) -> dict[str, set[str]]:
    """Get resource names from a remote repo via sparse clone."""
    names = {"skill": set(), "agent": set(), "rule": set(), "hook": set()}

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


# --- Filtering & Tiering ---


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


def tier_resource(name: str, resource_type: str, stacks: list[str]) -> str:
    """Assign a tier to a missing resource: must-have, nice-to-have, or skip.

    Returns one of: 'must-have', 'nice-to-have', 'skip'.
    """
    # Always-skip list
    if name in ALWAYS_SKIP:
        return "skip"

    # Wrong-stack resources
    if is_stack_specific(name) and not matches_stacks(name, stacks):
        return "skip"

    # Type-specific tiering
    if resource_type == "hook":
        if name in MUST_HAVE_HOOKS:
            return "must-have"
        return "nice-to-have"

    if resource_type == "agent":
        if name in MUST_HAVE_AGENTS:
            return "must-have"
        return "nice-to-have"

    if resource_type == "rule":
        if name in MUST_HAVE_RULES:
            return "must-have"
        return "nice-to-have"

    if resource_type == "skill":
        # Stack-specific overrides — some stack skills are nice-to-have, not must-have
        if name in NICE_TO_HAVE_STACK_OVERRIDES:
            return "nice-to-have"

        # Stack-specific skills matching the project's stacks are must-haves
        if is_stack_specific(name) and matches_stacks(name, stacks):
            return "must-have"

        if name in MUST_HAVE_UNIVERSAL_SKILLS:
            return "must-have"

        if name in NICE_TO_HAVE_UNIVERSAL_SKILLS:
            return "nice-to-have"

        # Remaining universal skills not in any list — nice-to-have
        return "nice-to-have"

    return "nice-to-have"


# --- Gap Analysis ---


def analyze_gaps(
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    stacks: list[str],
) -> dict[str, list[dict]]:
    """Compare hub resources against project resources and tier the gaps.

    Returns dict with keys 'must-have', 'nice-to-have', 'skip', each containing
    a list of {'name': str, 'type': str, 'tier': str}.
    """
    gaps = {"must-have": [], "nice-to-have": [], "skip": []}

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            name = resource["name"]

            # Skip if project already has it (accounting for name variations)
            if name_matches_existing(name, project_names.get(resource_type, set())):
                continue

            # Skip if it doesn't match the project's stacks
            if not matches_stacks(name, stacks):
                gaps["skip"].append({
                    "name": name, "type": resource_type, "tier": "skip",
                    "reason": "wrong stack",
                })
                continue

            tier = tier_resource(name, resource_type, stacks)
            gaps[tier].append({
                "name": name, "type": resource_type, "tier": tier,
            })

    return gaps


# --- Report ---


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
    lines.append(f"TOTAL: {len(must)} must-have, {len(nice)} nice-to-have, {len(skip)} skip")
    lines.append("=" * 60)

    return "\n".join(lines)


# --- Apply ---


def apply_to_local(
    hub_root: Path,
    target_dir: Path,
    gaps: dict[str, list[dict]],
    tier: str = "must-have",
) -> list[str]:
    """Copy recommended resources from hub to a local project directory.

    Only copies resources at or above the specified tier.
    """
    copied = []
    claude_src = hub_root / "core" / ".claude"

    tiers_to_apply = ["must-have"]
    if tier == "nice-to-have":
        tiers_to_apply.append("nice-to-have")

    for t in tiers_to_apply:
        for item in gaps.get(t, []):
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
                else:
                    print(f"  WARNING: hub skill '{name}' not found at {src}")

            elif rtype == "agent":
                src = claude_src / "agents" / f"{name}.md"
                dst = target_dir / ".claude" / "agents" / f"{name}.md"
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/agents/{name}.md")
                else:
                    print(f"  WARNING: hub agent '{name}' not found at {src}")

            elif rtype == "rule":
                src = claude_src / "rules" / f"{name}.md"
                dst = target_dir / ".claude" / "rules" / f"{name}.md"
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/rules/{name}.md")
                else:
                    print(f"  WARNING: hub rule '{name}' not found at {src}")

            elif rtype == "hook":
                src = claude_src / "hooks" / f"{name}.sh"
                dst = target_dir / ".claude" / "hooks" / f"{name}.sh"
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/hooks/{name}.sh")
                else:
                    print(f"  WARNING: hub hook '{name}' not found at {src}")

    return copied


def apply_to_repo(
    hub_root: Path,
    repo: str,
    gaps: dict[str, list[dict]],
    tier: str = "must-have",
) -> Optional[str]:
    """Clone a repo, apply recommendations on a branch, and create a PR.

    Returns the PR URL if successful.
    """
    from scripts.sync_to_projects import check_existing_pr

    branch = "claude-recommendations"

    if check_existing_pr(repo, branch):
        print(f"PR already exists for branch '{branch}' on {repo}. Skipping.")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        # Full clone (need to push back)
        try:
            subprocess.run(
                ["git", "clone", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo}: {e}")
            return None

        # Create branch
        subprocess.run(
            ["git", "-C", tmpdir, "checkout", "-b", branch],
            capture_output=True, text=True, check=True,
        )

        # Copy resources
        copied = apply_to_local(hub_root, Path(tmpdir), gaps, tier)
        if not copied:
            print("No resources to copy.")
            return None

        # Commit
        subprocess.run(
            ["git", "-C", tmpdir, "add", ".claude/"],
            capture_output=True, text=True, check=True,
        )

        must_count = len(gaps.get("must-have", []))
        nice_count = len(gaps.get("nice-to-have", []))
        commit_msg = (
            f"feat: add {len(copied)} recommended Claude resources\n\n"
            f"Added {must_count} must-have and "
            f"{nice_count if tier == 'nice-to-have' else 0} nice-to-have resources "
            f"from claude-best-practices hub.\n\n"
            f"Files:\n" + "\n".join(f"  - {f}" for f in copied[:20])
        )
        if len(copied) > 20:
            commit_msg += f"\n  ... and {len(copied) - 20} more"

        subprocess.run(
            ["git", "-C", tmpdir, "commit", "-m", commit_msg],
            capture_output=True, text=True, check=True,
        )

        # Push
        subprocess.run(
            ["git", "-C", tmpdir, "push", "-u", "origin", branch],
            capture_output=True, text=True, check=True,
        )

        # Create PR
        pr_body = (
            "## Summary\n\n"
            f"Auto-generated recommendations from [claude-best-practices]"
            f"(https://github.com/abhayla/claude-best-practices) hub.\n\n"
            f"- **{must_count}** must-have resources\n"
            f"- **{nice_count if tier == 'nice-to-have' else 0}** nice-to-have resources\n\n"
            "## Files added\n\n"
            + "\n".join(f"- `{f}`" for f in copied[:30])
        )
        if len(copied) > 30:
            pr_body += f"\n- ... and {len(copied) - 30} more"

        result = subprocess.run(
            ["gh", "pr", "create",
             "--repo", repo,
             "--head", branch,
             "--title", f"feat: add {len(copied)} recommended Claude resources",
             "--body", pr_body],
            capture_output=True, text=True, timeout=30,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"PR creation failed: {result.stderr}")
            return None


# --- Content Diff ---


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


# --- Provision ---

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
) -> str:
    """Build the hub best-practices section for CLAUDE.md.

    Contains: Bug Fixing rule, dynamic Rules Reference table, sync metadata.
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
        "1. **Bug Fixing**: Use `/fix-loop` or `/fix-issue`. "
        "Start by writing a test that reproduces the bug, "
        "then fix and prove with a passing test."
    )
    lines.append("")

    # Dynamic rules reference table
    if rules_present:
        descriptions = get_rule_descriptions(hub_root, rules_present)
        lines.append("### Rules Reference")
        lines.append("")
        lines.append("| Rule File | What It Covers |")
        lines.append("|-----------|---------------|")
        for name in sorted(rules_present):
            desc = descriptions.get(name, name.replace("-", " ").title())
            lines.append(f"| `rules/{name}.md` | {desc} |")
        lines.append("")

    lines.append("## Claude Code Configuration")
    lines.append("")
    lines.append("The `.claude/` directory contains skills, agents, and rules for Claude Code.")
    lines.append("")
    lines.append(PROVISION_END_MARKER)
    return "\n".join(lines)


def provision_claude_md(
    hub_root: Path,
    target_dir: Path,
    stacks: list[str],
    rules_present: list[str],
) -> str:
    """Provision CLAUDE.md in the target directory.

    Three cases:
    1. No CLAUDE.md exists → create from template
    2. CLAUDE.md exists with markers → replace between markers
    3. CLAUDE.md exists without markers → append section with markers
    """
    claude_md = target_dir / "CLAUDE.md"
    hub_section = generate_hub_practices_section(hub_root, rules_present)

    if not claude_md.exists():
        # Case 1: Create from template
        template_path = hub_root / "core" / ".claude" / "CLAUDE.md.template"
        if template_path.exists():
            from datetime import datetime
            template = template_path.read_text(encoding="utf-8")
            rendered = render_template(template, {
                "PROJECT_NAME": target_dir.name,
                "PROJECT_DESCRIPTION": "A new project",
                "PLATFORM": ", ".join(stacks) if stacks else "general",
                "BUILD_TOOLS": "See stack documentation",
                "DEVELOPMENT_COMMANDS": "# Add your commands here",
                "HUB_REPO": "abhayla/claude-best-practices",
                "SELECTED_STACKS": ", ".join(stacks) if stacks else "none",
                "LAST_SYNC_TIMESTAMP": datetime.utcnow().isoformat(),
            })
            claude_md.write_text(rendered, encoding="utf-8")
            return "created"
        else:
            claude_md.write_text(f"# CLAUDE.md\n\n{hub_section}\n", encoding="utf-8")
            return "created"

    # File exists — read it
    content = claude_md.read_text(encoding="utf-8")

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


def provision_settings_json(hub_root: Path, target_dir: Path) -> str:
    """Provision .claude/settings.json by merging hub defaults with existing."""
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
        return "merged"

    target_settings_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(hub_settings_path, target_settings_path)
    return "created"


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


def provision_to_local(
    hub_root: Path,
    target_dir: Path,
    gaps: dict[str, list[dict]],
    stacks: list[str],
    tier: str = "must-have",
) -> dict:
    """Orchestrate full provisioning to a local directory.

    Copies resources, provisions CLAUDE.md, CLAUDE.local.md, and settings.json.
    Returns a summary dict.
    """
    # Step 1: Copy resources
    copied = apply_to_local(hub_root, target_dir, gaps, tier)

    # Determine which rules are present after copying
    project_names = get_project_resource_names(target_dir / ".claude")
    rules_present = sorted(project_names.get("rule", set()))

    # Step 2: Provision CLAUDE.md
    claude_md_status = provision_claude_md(hub_root, target_dir, stacks, rules_present)

    # Step 3: Provision CLAUDE.local.md
    claude_local_status = provision_claude_local_md(hub_root, target_dir)

    # Step 4: Provision settings.json
    settings_status = provision_settings_json(hub_root, target_dir)

    return {
        "copied_files": copied,
        "claude_md": claude_md_status,
        "claude_local_md": claude_local_status,
        "settings_json": settings_status,
    }


def provision_to_repo(
    hub_root: Path,
    repo: str,
    gaps: dict[str, list[dict]],
    stacks: list[str],
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    tier: str = "must-have",
) -> Optional[str]:
    """Clone a repo, provision resources + config files, and create a PR.

    Returns the PR URL if successful.
    """
    from scripts.sync_to_projects import check_existing_pr

    branch = "claude-provision"

    if check_existing_pr(repo, branch):
        print(f"PR already exists for branch '{branch}' on {repo}. Skipping.")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo}: {e}")
            return None

        subprocess.run(
            ["git", "-C", tmpdir, "checkout", "-b", branch],
            capture_output=True, text=True, check=True,
        )

        # Full provision
        summary = provision_to_local(hub_root, Path(tmpdir), gaps, stacks, tier)
        copied = summary["copied_files"]

        # Analyze overlaps for PR body
        updated_project_names = get_project_resource_names(Path(tmpdir) / ".claude")
        overlaps = analyze_overlaps_local(
            hub_root, Path(tmpdir), hub_resources, updated_project_names
        )
        divergence_table = format_divergence_table(overlaps)

        # Git add — only include tracked/trackable files
        # Note: CLAUDE.local.md is typically gitignored (personal prefs), so skip it
        add_paths = []
        if (Path(tmpdir) / ".claude").exists():
            add_paths.append(".claude/")
        if (Path(tmpdir) / "CLAUDE.md").exists():
            add_paths.append("CLAUDE.md")
        if not add_paths:
            print("Nothing to provision — no files to stage.")
            return None
        result = subprocess.run(
            ["git", "-C", tmpdir, "add"] + add_paths,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"git add failed: {result.stderr}")
            return None

        # Check if there are staged changes — skip PR if nothing changed
        status_result = subprocess.run(
            ["git", "-C", tmpdir, "diff", "--cached", "--quiet"],
            capture_output=True, text=True,
        )
        if status_result.returncode == 0:
            # No staged changes
            print("Nothing to provision — project is already up to date.")
            return None

        must_count = len(gaps.get("must-have", []))
        nice_count = len(gaps.get("nice-to-have", []))
        commit_msg = (
            f"feat: provision {len(copied)} Claude resources + config\n\n"
            f"Added {must_count} must-have and "
            f"{nice_count if tier == 'nice-to-have' else 0} nice-to-have resources.\n"
            f"CLAUDE.md: {summary['claude_md']}\n"
            f"CLAUDE.local.md: {summary['claude_local_md']}\n"
            f"settings.json: {summary['settings_json']}\n\n"
            f"Files:\n" + "\n".join(f"  - {f}" for f in copied[:20])
        )
        if len(copied) > 20:
            commit_msg += f"\n  ... and {len(copied) - 20} more"

        subprocess.run(
            ["git", "-C", tmpdir, "commit", "-m", commit_msg],
            capture_output=True, text=True, check=True,
        )

        subprocess.run(
            ["git", "-C", tmpdir, "push", "-u", "origin", branch],
            capture_output=True, text=True, check=True,
        )

        pr_body = (
            "## Summary\n\n"
            f"Auto-provisioned from [claude-best-practices]"
            f"(https://github.com/abhayla/claude-best-practices) hub.\n\n"
            f"- **{must_count}** must-have resources\n"
            f"- **{nice_count if tier == 'nice-to-have' else 0}** nice-to-have resources\n"
            f"- CLAUDE.md: {summary['claude_md']}\n"
            f"- CLAUDE.local.md: {summary['claude_local_md']}\n"
            f"- settings.json: {summary['settings_json']}\n\n"
            "## Files added\n\n"
            + "\n".join(f"- `{f}`" for f in copied[:30])
        )
        if len(copied) > 30:
            pr_body += f"\n- ... and {len(copied) - 30} more"

        if divergence_table:
            pr_body += f"\n\n{divergence_table}"

        result = subprocess.run(
            ["gh", "pr", "create",
             "--repo", repo,
             "--head", branch,
             "--title", f"feat: provision {len(copied)} Claude resources + config",
             "--body", pr_body],
            capture_output=True, text=True, timeout=30,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"PR creation failed: {result.stderr}")
            return None


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        description="Recommend Claude resources for a project based on tech stack analysis"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="GitHub repo (owner/name)")
    group.add_argument("--local", help="Local project directory path")

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--apply", action="store_true",
                              help="Apply recommendations (copy files or create PR)")
    action_group.add_argument("--provision", action="store_true",
                              help="Provision project (apply + CLAUDE.md + settings.json)")
    parser.add_argument("--tier", choices=["must-have", "nice-to-have"],
                        default="must-have",
                        help="Minimum tier to apply (default: must-have)")
    parser.add_argument("--use-config", action="store_true",
                        help="Use stacks from config/repos.yml instead of auto-detection")
    parser.add_argument("--diff", action="store_true",
                        help="Compare content of overlapping resources to detect divergence")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")

    args = parser.parse_args()
    hub_root = Path(__file__).parent.parent

    # Step 1: Detect stacks
    stacks = None
    if args.use_config and args.repo:
        config_path = hub_root / "config" / "repos.yml"
        stacks = get_stacks_from_config(args.repo, config_path)
        if stacks:
            print(f"Stacks from config: {', '.join(stacks)}")
        else:
            print(f"Repo '{args.repo}' not found in config/repos.yml, falling back to auto-detection")

    if stacks is None:
        if args.local:
            stacks = detect_stacks_from_dir(Path(args.local))
        else:
            stacks = detect_stacks_from_repo(args.repo)
        print(f"Auto-detected stacks: {', '.join(stacks) if stacks else 'none'}")

    # Step 2: Get project resources
    if args.local:
        project_names = get_project_resource_names(Path(args.local) / ".claude")
    else:
        project_names = get_project_resources_from_repo(args.repo)

    existing_count = sum(len(v) for v in project_names.values())
    print(f"Project has {existing_count} existing resources")

    # Step 3: Get hub resources
    hub_resources = get_hub_resources(hub_root)

    # Step 4: Analyze gaps
    gaps = analyze_gaps(hub_resources, project_names, stacks)

    # Step 5: Output
    if args.json_output:
        print(json.dumps(gaps, indent=2))
    else:
        report = format_report(gaps, stacks, project_names, hub_resources)
        print()
        print(report)

    # Step 6: Apply if requested
    if args.apply:
        print(f"\nApplying {args.tier} tier recommendations...")
        if args.local:
            copied = apply_to_local(hub_root, Path(args.local), gaps, args.tier)
            print(f"Copied {len(copied)} files to {args.local}/.claude/")
            for f in copied:
                print(f"  + {f}")
        else:
            pr_url = apply_to_repo(hub_root, args.repo, gaps, args.tier)
            if pr_url:
                print(f"PR created: {pr_url}")

    # Step 6b: Provision if requested
    if args.provision:
        print(f"\nProvisioning {args.tier} tier resources + config files...")
        if args.local:
            summary = provision_to_local(hub_root, Path(args.local), gaps, stacks, args.tier)
            print(f"Copied {len(summary['copied_files'])} files to {args.local}/.claude/")
            for f in summary["copied_files"]:
                print(f"  + {f}")
            print(f"CLAUDE.md: {summary['claude_md']}")
            print(f"CLAUDE.local.md: {summary['claude_local_md']}")
            print(f"settings.json: {summary['settings_json']}")
        else:
            pr_url = provision_to_repo(
                hub_root, args.repo, gaps, stacks,
                hub_resources, project_names, args.tier,
            )
            if pr_url:
                print(f"PR created: {pr_url}")

    # Step 7: Diff overlapping resources if requested
    if args.diff:
        print("\nAnalyzing content divergence for overlapping resources...")
        if args.local:
            overlaps = analyze_overlaps_local(
                hub_root, Path(args.local), hub_resources, project_names
            )
        else:
            overlaps = analyze_overlaps_repo(
                hub_root, args.repo, hub_resources, project_names
            )

        if args.json_output:
            # Strip non-serializable fields
            print(json.dumps(overlaps, indent=2))
        else:
            diff_report = format_diff_report(overlaps)
            print()
            print(diff_report)


if __name__ == "__main__":
    main()
