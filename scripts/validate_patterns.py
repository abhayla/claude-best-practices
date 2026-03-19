"""Pattern quality validator for core/.claude/ patterns.

Validates skills, agents, and rules against portability, structure,
self-containment, and versioning standards. Can be run standalone or
from CI via validate-pr.yml.

Usage:
    PYTHONPATH=. python scripts/validate_patterns.py
    PYTHONPATH=. python scripts/validate_patterns.py --fix-suggestions
    PYTHONPATH=. python scripts/validate_patterns.py path/to/pattern.md
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
SKILLS_DIR = CORE_CLAUDE / "skills"
AGENTS_DIR = CORE_CLAUDE / "agents"
RULES_DIR = CORE_CLAUDE / "rules"
REGISTRY_PATH = ROOT / "registry" / "patterns.json"

# Thresholds
SIZE_WARN = 500
SIZE_FAIL = 1000
STUB_MIN_LINES = 30

# Known stack prefixes
STACK_PREFIXES = ["fastapi-", "android-", "ai-gemini-", "firebase-", "react-", "flutter-", "vue-", "nuxt-", "expo-"]

# Hub-only patterns that MUST NOT appear in core/.claude/ (distributable template).
# These are operational skills/rules for managing the hub itself, not for downstream projects.
HUB_ONLY_SKILLS = {"synthesize-hub", "scan-repo", "scan-url"}
HUB_ONLY_RULES = set()
HUB_ONLY_AGENTS = set()

# Portability: patterns that indicate hardcoded paths (not in code blocks)
HARDCODED_PATH_PATTERNS = [
    r"(?<![`\w])[A-Z]:\\[\w\\]+",           # Windows absolute paths like C:\Users\...
    r"(?<![`\w])/home/\w+",                   # Linux home dirs
    r"(?<![`\w])/Users/\w+",                  # macOS home dirs
]

# Patterns for placeholder/TODO markers
PLACEHOLDER_PATTERNS = [
    r"<!--\s*TODO:",
    r"<!--\s*FIXME:",
    r"<!--\s*PLACEHOLDER",
]


def parse_frontmatter(file_path: Path) -> Optional[dict]:
    """Extract YAML frontmatter from a markdown file."""
    content = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def get_body(file_path: Path) -> str:
    """Get the markdown body after frontmatter."""
    content = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)", content, re.DOTALL)
    return match.group(1) if match else content


def count_content_lines(file_path: Path) -> int:
    """Count non-empty, non-heading lines in the body (excluding frontmatter)."""
    body = get_body(file_path)
    lines = body.splitlines()
    return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))


def is_valid_semver(version: str) -> bool:
    """Check if version string is valid semver."""
    return bool(re.match(r"^\d+\.\d+\.\d+$", str(version)))


# ── Skill Validators ────────────────────────────────────────────────────────


def validate_skill(skill_dir: Path) -> list[str]:
    """Validate a single skill directory. Returns list of errors."""
    errors = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return [f"{skill_dir.name}: Missing SKILL.md"]

    fm = parse_frontmatter(skill_md)
    if fm is None:
        return [f"{skill_dir.name}: Missing or invalid YAML frontmatter"]

    name = skill_dir.name

    # Required frontmatter fields
    if "name" not in fm:
        errors.append(f"{name}: Missing 'name' in frontmatter")
    elif fm["name"] != name:
        errors.append(f"{name}: Frontmatter name '{fm['name']}' doesn't match directory '{name}'")

    if "description" not in fm:
        errors.append(f"{name}: Missing 'description' in frontmatter")

    if "allowed-tools" not in fm:
        errors.append(f"{name}: Missing 'allowed-tools' in frontmatter")

    if "argument-hint" not in fm:
        errors.append(f"{name}: Missing 'argument-hint' in frontmatter")

    if "version" not in fm:
        errors.append(f"{name}: Missing 'version' in frontmatter")
    elif not is_valid_semver(fm["version"]):
        errors.append(f"{name}: Invalid semver '{fm['version']}' — expected format: 1.0.0")

    if "type" not in fm:
        errors.append(f"{name}: Missing 'type' in frontmatter — must be 'workflow' or 'reference'")
    elif fm["type"] not in ("workflow", "reference"):
        errors.append(f"{name}: Invalid type '{fm['type']}' — must be 'workflow' or 'reference'")

    # Type-specific structure checks
    body = get_body(skill_md)
    has_steps = bool(re.search(r"^##\s+STEP\s+\d+", body, re.MULTILINE))

    if fm.get("type") == "workflow" and not has_steps:
        errors.append(f"{name}: Type is 'workflow' but no '## STEP N:' sections found")

    # Size check
    total_lines = len(skill_md.read_text(encoding="utf-8").splitlines())
    if total_lines > SIZE_FAIL:
        errors.append(f"{name}: SKILL.md is {total_lines} lines (max {SIZE_FAIL}) — split into smaller files or use references/ subdirectory")
    elif total_lines > SIZE_WARN:
        errors.append(f"{name}: WARNING — SKILL.md is {total_lines} lines (recommended max {SIZE_WARN})")

    # Placeholder detection (skip code blocks and inline code)
    content = skill_md.read_text(encoding="utf-8")
    content_stripped = re.sub(r"```[\s\S]*?```", "", content)  # fenced code blocks
    content_stripped = re.sub(r"`[^`]+`", "", content_stripped)  # inline code
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content_stripped, re.IGNORECASE):
            errors.append(f"{name}: Contains placeholder marker matching '{pattern}' — patterns must be complete before merging")

    # Stub detection
    content_lines = count_content_lines(skill_md)
    if content_lines < STUB_MIN_LINES:
        errors.append(f"{name}: Only {content_lines} content lines — appears to be a stub (min {STUB_MIN_LINES})")

    # Least-privilege tool check
    allowed_tools = str(fm.get("allowed-tools", ""))
    write_tools = {"Write", "Edit", "Bash"}
    listed_write_tools = [t for t in write_tools if t in allowed_tools]
    if listed_write_tools:
        # Check if body actually references these tools
        for tool in listed_write_tools:
            # Look for actual usage patterns (tool names in steps, not just in frontmatter)
            tool_usage_patterns = [
                rf"\b{tool}\b.*tool",
                rf"use.*\b{tool}\b",
                rf"\b{tool}\(",
            ]
            body_lower = body.lower()
            tool_lower = tool.lower()
            # Simple heuristic: if the tool name appears in the body outside of frontmatter
            if tool_lower not in body_lower and fm.get("type") == "reference":
                errors.append(f"{name}: Type is 'reference' but '{tool}' is in allowed-tools — reference skills should be read-only")

    return errors


# ── Agent Validators ────────────────────────────────────────────────────────


def validate_agent(agent_path: Path) -> list[str]:
    """Validate a single agent file. Returns list of errors."""
    errors = []
    name = agent_path.stem

    fm = parse_frontmatter(agent_path)
    if fm is None:
        errors.append(f"{name}: Missing or invalid YAML frontmatter")
        return errors

    if "name" not in fm:
        errors.append(f"{name}: Missing 'name' in frontmatter")

    if "description" not in fm:
        errors.append(f"{name}: Missing 'description' in frontmatter")

    if "model" not in fm:
        errors.append(f"{name}: Missing 'model' in frontmatter — must be inherit, sonnet, haiku, or opus")
    elif fm["model"] not in ("inherit", "sonnet", "haiku", "opus"):
        errors.append(f"{name}: Invalid model '{fm['model']}' — must be inherit, sonnet, haiku, or opus")

    return errors


# ── Rule Validators ─────────────────────────────────────────────────────────


def validate_rule(rule_path: Path) -> list[str]:
    """Validate a single rule file. Returns list of errors."""
    errors = []
    name = rule_path.stem
    content = rule_path.read_text(encoding="utf-8")

    fm = parse_frontmatter(rule_path)

    # Check scope declaration (globs: or paths: both valid)
    has_globs = fm and ("globs" in fm or "paths" in fm)
    first_lines = "\n".join(content.splitlines()[:10])
    has_scope_global = "# Scope: global" in first_lines

    if not has_globs and not has_scope_global:
        errors.append(f"{name}: Missing scope — add 'globs:' in frontmatter or '# Scope: global' in first 5 lines")

    # Placeholder detection (skip code blocks and inline code)
    content_stripped = re.sub(r"```[\s\S]*?```", "", content)  # fenced code blocks
    content_stripped = re.sub(r"`[^`]+`", "", content_stripped)  # inline code
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content_stripped, re.IGNORECASE):
            errors.append(f"{name}: Contains placeholder marker — rules must be complete before merging")

    # Stub detection — count non-empty, non-heading, non-frontmatter lines
    body_lines = content.split("---", 2)[-1] if "---" in content else content
    content_lines = sum(1 for line in body_lines.splitlines()
                       if line.strip() and not line.strip().startswith("#"))
    if content_lines < 5:
        errors.append(f"{name}: Only {content_lines} content lines — appears to be a stub")

    return errors


# ── Portability Validators ──────────────────────────────────────────────────


def check_portability(file_path: Path) -> list[str]:
    """Check a pattern file for portability issues."""
    errors = []
    name = file_path.stem if file_path.suffix == ".md" else file_path.parent.name
    content = file_path.read_text(encoding="utf-8")

    # Remove code blocks before checking (hardcoded paths in examples are OK)
    content_no_codeblocks = re.sub(r"```[\s\S]*?```", "", content)

    for pattern in HARDCODED_PATH_PATTERNS:
        matches = re.findall(pattern, content_no_codeblocks)
        if matches:
            errors.append(f"{name}: Hardcoded path(s) found outside code blocks: {matches[:3]}")

    return errors


# ── Cross-Reference Validator ───────────────────────────────────────────────


def check_cross_references(skills_dir: Path) -> list[str]:
    """Check that all skill cross-references point to existing skills."""
    errors = []
    existing_skills = set()

    # Words that look like skill references but are generic terms or placeholders
    IGNORE_REFS = {
        "name", "skill-name", "removed-skill",  # template placeholders
        "clear", "docs", "redoc", "metrics", "proc",  # generic single words
        "login", "settings", "public", "test", "build",  # common non-skill terms
    }

    # Hub-only skills that exist in .claude/skills/ (not core/.claude/skills/) and
    # are valid cross-reference targets even though they won't be in the distributable
    # template. Skills referencing these are hub-aware and the references are intentional.
    HUB_ONLY_VALID_REFS = {"synthesize-hub", "scan-repo", "scan-url"}

    if skills_dir.exists():
        existing_skills = {d.name for d in skills_dir.iterdir()
                          if d.is_dir() and (d / "SKILL.md").exists()}

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        content = skill_md.read_text(encoding="utf-8")
        # Remove code blocks to avoid matching examples/templates
        content_no_codeblocks = re.sub(r"```[\s\S]*?```", "", content)

        # Find Skill() delegations (only outside code blocks)
        refs = re.findall(r'Skill\(["\']([^"\']+)["\']', content_no_codeblocks)
        # Find /skill-name references in backticks (only outside code blocks)
        refs += re.findall(r'`/([a-z][a-z0-9-]+)`', content_no_codeblocks)
        # Find "delegate to /skill-name" patterns
        refs += re.findall(r'delegate to /([a-z][a-z0-9-]+)', content_no_codeblocks, re.IGNORECASE)

        for ref in set(refs):
            # Skip placeholders, generic words, and angle-bracket templates
            if ref in IGNORE_REFS or ref.startswith("<") or len(ref) < 4:
                continue
            # Skip hub-only skills that are valid references but not in core/.claude/
            if ref in HUB_ONLY_VALID_REFS:
                continue
            if ref not in existing_skills:
                errors.append(f"{skill_dir.name}: References non-existent skill '{ref}'")

    return errors


# ── Single-File Validator ───────────────────────────────────────────────────


def _looks_like_agent(file_path: Path) -> bool:
    """Check if a markdown file looks like an agent (has 'model' in frontmatter)."""
    fm = parse_frontmatter(file_path)
    return fm is not None and "model" in fm


def validate_file(file_path: Path) -> list[str]:
    """Validate a single pattern file. Auto-detects type (skill/agent/rule).

    Returns list of error strings (empty = valid).
    """
    path = Path(file_path)
    if not path.exists():
        return [f"File not found: {path}"]

    errors = []

    if path.name == "SKILL.md":
        errors.extend(validate_skill(path.parent))
    elif _looks_like_agent(path):
        errors.extend(validate_agent(path))
    else:
        errors.extend(validate_rule(path))

    errors.extend(check_portability(path))
    return errors


# ── Main ────────────────────────────────────────────────────────────────────


def validate_third_party_registry() -> list[str]:
    """Validate config/third-party-skills.yml if it exists."""
    from scripts.third_party_skills import validate_registry
    return validate_registry(ROOT)


def validate_all() -> list[str]:
    """Run all validators. Returns list of all errors."""
    all_errors = []

    # Validate skills
    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            if skill_dir.name in HUB_ONLY_SKILLS:
                all_errors.append(
                    f"{skill_dir.name}: Hub-only skill found in core/.claude/skills/ — "
                    f"this belongs in .claude/skills/ (hub-only, not distributed)"
                )
                continue
            all_errors.extend(validate_skill(skill_dir))
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                all_errors.extend(check_portability(skill_md))

    # Validate agents
    if AGENTS_DIR.exists():
        for agent_path in sorted(AGENTS_DIR.glob("*.md")):
            if agent_path.name == "README.md":
                continue
            if agent_path.stem in HUB_ONLY_AGENTS:
                all_errors.append(
                    f"{agent_path.stem}: Hub-only agent found in core/.claude/agents/ — "
                    f"this belongs in .claude/agents/ (hub-only, not distributed)"
                )
                continue
            all_errors.extend(validate_agent(agent_path))
            all_errors.extend(check_portability(agent_path))

    # Validate rules
    if RULES_DIR.exists():
        for rule_path in sorted(RULES_DIR.glob("*.md")):
            if rule_path.name == "README.md":
                continue
            if rule_path.stem in HUB_ONLY_RULES:
                all_errors.append(
                    f"{rule_path.stem}: Hub-only rule found in core/.claude/rules/ — "
                    f"this belongs in .claude/rules/ (hub-only, not distributed)"
                )
                continue
            all_errors.extend(validate_rule(rule_path))
            all_errors.extend(check_portability(rule_path))

    # Cross-reference check
    if SKILLS_DIR.exists():
        all_errors.extend(check_cross_references(SKILLS_DIR))

    # Third-party skills registry validation
    all_errors.extend(validate_third_party_registry())

    return all_errors


def main():
    parser = argparse.ArgumentParser(description="Pattern quality validator")
    parser.add_argument("file", nargs="?", default=None,
                        help="Single pattern file to validate (auto-detects type)")
    parser.add_argument("--fix-suggestions", action="store_true",
                        help="Show suggested fixes for errors")
    args = parser.parse_args()

    if args.file:
        # Single-file validation mode
        target = Path(args.file)
        print(f"Validating: {target}")
        errors = validate_file(target)
        warnings = [e for e in errors if "WARNING" in e]
        hard_errors = [e for e in errors if "WARNING" not in e]
        if warnings:
            for w in warnings:
                print(f"  WARN: {w}")
        if hard_errors:
            for e in hard_errors:
                print(f"  FAIL: {e}")
            print(f"\nFAILED: {len(hard_errors)} error(s), {len(warnings)} warning(s)")
            sys.exit(1)
        else:
            print(f"PASSED ({len(warnings)} warning(s))")
            sys.exit(0)

    # Full validation mode (existing behavior)
    print("=" * 60)
    print("Pattern Quality Validator")
    print("=" * 60)

    errors = validate_all()

    warnings = [e for e in errors if "WARNING" in e]
    hard_errors = [e for e in errors if "WARNING" not in e]

    if warnings:
        print(f"\nWARNINGS: {len(warnings)} warning(s):")
        for w in sorted(warnings):
            print(f"  WARN: {w}")

    if hard_errors:
        print(f"\nFAILED: {len(hard_errors)} error(s):")
        for e in sorted(hard_errors):
            print(f"  FAIL: {e}")

        if args.fix_suggestions:
            print("\nSuggested fixes:")
            for e in sorted(hard_errors):
                if "Missing 'version'" in e:
                    print(f"  → Add 'version: \"1.0.0\"' to frontmatter")
                elif "Missing 'type'" in e:
                    print(f"  → Add 'type: workflow' or 'type: reference' to frontmatter")
                elif "Missing scope" in e:
                    print(f"  → Add 'globs:' to frontmatter or '# Scope: global' to first 5 lines")

        print(f"\nTotal: {len(hard_errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        print(f"\nPASSED: All patterns valid ({len(warnings)} warning(s))")
        sys.exit(0)


if __name__ == "__main__":
    main()
