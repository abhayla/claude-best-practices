"""Pattern quality validator for core/.claude/ patterns.

Validates skills, agents, and rules against portability, structure,
self-containment, and versioning standards. Can be run standalone or
from CI via validate-pr.yml.

Usage:
    PYTHONPATH=. python scripts/validate_patterns.py
    PYTHONPATH=. python scripts/validate_patterns.py --fix-suggestions
    PYTHONPATH=. python scripts/validate_patterns.py --score
    PYTHONPATH=. python scripts/validate_patterns.py --baseline-save
    PYTHONPATH=. python scripts/validate_patterns.py --baseline
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

BASELINE_PATH = ROOT / ".pattern-baseline.json"

# Description quality: vague words that indicate a generic summary, not a trigger condition
VAGUE_DESCRIPTION_WORDS = {
    "helper", "utility", "tool", "handler", "manager", "misc",
    "various", "general", "stuff", "things",
}

# Description quality: action verbs that a good description should start with
ACTION_VERBS = {
    "run", "generate", "analyze", "validate", "create", "build", "check",
    "scan", "deploy", "test", "audit", "review", "execute", "configure",
    "detect", "enforce", "extract", "implement", "launch", "manage",
    "monitor", "optimize", "parse", "provision", "scaffold", "search",
    "set", "verify", "write", "compose", "compute", "consume", "craft",
    "debug", "discover", "fix", "inspect", "iterate", "migrate", "plan",
    "post", "read", "recommend", "resume", "route", "save", "score",
    "organize", "fetch", "collect", "guide", "orchestrate", "convert",
    "initialize", "restore", "resume", "trigger", "setup", "scaffold",
    "auto", "apply", "push", "pull", "compare", "trace", "measure",
    "design", "diagnose", "author", "finalize", "inject", "integrate",
    "assess", "capture", "classify", "define", "explore", "identify",
}


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


# ── Description Quality ────────────────────────────────────────────────────


def check_description_quality(name: str, description: str) -> list[str]:
    """Check if a skill description is a trigger condition, not a generic summary."""
    errors = []
    if not description:
        return errors

    first_word = description.split()[0].lower().rstrip("s").rstrip(",.:;")
    if first_word not in ACTION_VERBS and first_word + "s" not in ACTION_VERBS:
        errors.append(
            f"{name}: WARNING — description should start with an action verb "
            f"(e.g., Run, Generate, Analyze), got '{description.split()[0]}'"
        )

    desc_lower = description.lower()
    if "when" not in desc_lower and "use " not in desc_lower:
        errors.append(
            f"{name}: WARNING — description should include a 'when' or 'use when' "
            f"clause to help Claude discover and trigger the skill"
        )

    for vague in VAGUE_DESCRIPTION_WORDS:
        if re.search(rf"\b{vague}\b", desc_lower):
            errors.append(
                f"{name}: WARNING — description contains vague word '{vague}' "
                f"— use specific language instead"
            )

    if len(description) > 1024:
        errors.append(
            f"{name}: Description is {len(description)} chars (max 1024)"
        )

    return errors


# ── Quality Scoring ───────────────────────────────────────────────────────


def score_skill(skill_dir: Path) -> tuple[int, list[str]]:
    """Score a skill 0-100. Returns (score, breakdown)."""
    breakdown = []
    score = 100
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return 0, ["Missing SKILL.md (-100)"]

    fm = parse_frontmatter(skill_md)
    if fm is None:
        return 0, ["Missing frontmatter (-100)"]

    name = skill_dir.name

    # Frontmatter fields (6 required, -8 each missing = max -48)
    required = ["name", "description", "type", "allowed-tools", "argument-hint", "version"]
    for field in required:
        if field not in fm:
            score -= 8
            breakdown.append(f"Missing '{field}' (-8)")

    # Name matches directory (-5)
    if fm.get("name") and fm["name"] != name:
        score -= 5
        breakdown.append(f"Name mismatch (-5)")

    # Valid semver (-5)
    if fm.get("version") and not is_valid_semver(fm["version"]):
        score -= 5
        breakdown.append(f"Invalid semver (-5)")

    # Type-specific structure (-10)
    body = get_body(skill_md)
    has_steps = bool(re.search(r"^##\s+STEP\s+\d+", body, re.MULTILINE))
    if fm.get("type") == "workflow" and not has_steps:
        score -= 10
        breakdown.append(f"Workflow type without STEP sections (-10)")

    # Critical rules section (-5)
    has_critical = bool(re.search(
        r"^##\s+(CRITICAL RULES|MUST DO|MUST NOT DO)", body, re.MULTILINE
    ))
    if not has_critical:
        score -= 5
        breakdown.append(f"Missing CRITICAL RULES section (-5)")

    # Description quality (-3 each, max -9)
    desc = str(fm.get("description", "")).strip()
    if desc:
        first_word = desc.split()[0].lower().rstrip("s").rstrip(",.:;")
        if first_word not in ACTION_VERBS and first_word + "s" not in ACTION_VERBS:
            score -= 3
            breakdown.append(f"Description doesn't start with action verb (-3)")
        if "when" not in desc.lower() and "use " not in desc.lower():
            score -= 3
            breakdown.append(f"Description missing 'when' clause (-3)")
        for vague in VAGUE_DESCRIPTION_WORDS:
            if re.search(rf"\b{vague}\b", desc.lower()):
                score -= 3
                breakdown.append(f"Description uses vague word '{vague}' (-3)")
                break

    # Size penalties
    total_lines = len(skill_md.read_text(encoding="utf-8").splitlines())
    if total_lines > SIZE_FAIL:
        score -= 15
        breakdown.append(f"Over {SIZE_FAIL} lines (-15)")
    elif total_lines > SIZE_WARN:
        score -= 5
        breakdown.append(f"Over {SIZE_WARN} lines (-5)")

    # Stub penalty
    content_lines = count_content_lines(skill_md)
    if content_lines < STUB_MIN_LINES:
        score -= 15
        breakdown.append(f"Stub: only {content_lines} content lines (-15)")

    # Portability
    port_errors = check_portability(skill_md)
    if port_errors:
        score -= 5
        breakdown.append(f"Portability issues (-5)")

    # Placeholder markers
    content = skill_md.read_text(encoding="utf-8")
    content_stripped = re.sub(r"```[\s\S]*?```", "", content)
    content_stripped = re.sub(r"`[^`]+`", "", content_stripped)
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content_stripped, re.IGNORECASE):
            score -= 10
            breakdown.append(f"Contains placeholder markers (-10)")
            break

    return max(0, score), breakdown


def score_agent(agent_path: Path) -> tuple[int, list[str]]:
    """Score an agent 0-100. Returns (score, breakdown)."""
    breakdown = []
    score = 100

    fm = parse_frontmatter(agent_path)
    if fm is None:
        return 0, ["Missing frontmatter (-100)"]

    required = ["name", "description", "model"]
    for field in required:
        if field not in fm:
            score -= 15
            breakdown.append(f"Missing '{field}' (-15)")

    if fm.get("model") and fm["model"] not in ("inherit", "sonnet", "haiku", "opus"):
        score -= 10
        breakdown.append(f"Invalid model value (-10)")

    body = get_body(agent_path)
    if "## Core Responsibilities" not in body:
        score -= 10
        breakdown.append(f"Missing '## Core Responsibilities' section (-10)")
    if "## Output Format" not in body:
        score -= 10
        breakdown.append(f"Missing '## Output Format' section (-10)")

    desc = str(fm.get("description", "")).lower()
    if "when" not in desc and "use " not in desc:
        score -= 5
        breakdown.append(f"Description missing 'when' clause (-5)")

    port_errors = check_portability(agent_path)
    if port_errors:
        score -= 5
        breakdown.append(f"Portability issues (-5)")

    return max(0, score), breakdown


def score_rule(rule_path: Path) -> tuple[int, list[str]]:
    """Score a rule 0-100. Returns (score, breakdown)."""
    breakdown = []
    score = 100

    content = rule_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(rule_path)

    has_globs = fm and ("globs" in fm or "paths" in fm)
    first_lines = "\n".join(content.splitlines()[:10])
    has_scope_global = "# Scope: global" in first_lines

    if not has_globs and not has_scope_global:
        score -= 20
        breakdown.append(f"Missing scope declaration (-20)")

    body_lines = content.split("---", 2)[-1] if "---" in content else content
    content_lines = sum(1 for line in body_lines.splitlines()
                        if line.strip() and not line.strip().startswith("#"))
    if content_lines < 5:
        score -= 20
        breakdown.append(f"Stub: only {content_lines} content lines (-20)")

    content_stripped = re.sub(r"```[\s\S]*?```", "", content)
    content_stripped = re.sub(r"`[^`]+`", "", content_stripped)
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content_stripped, re.IGNORECASE):
            score -= 15
            breakdown.append(f"Contains placeholder markers (-15)")
            break

    port_errors = check_portability(rule_path)
    if port_errors:
        score -= 5
        breakdown.append(f"Portability issues (-5)")

    if not re.search(r"\bMUST\b|\bNEVER\b|\bMUST NOT\b", content):
        score -= 5
        breakdown.append(f"No directive language (MUST/NEVER) found (-5)")

    return max(0, score), breakdown


def grade(score: int) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_all() -> dict[str, dict]:
    """Score all patterns. Returns {name: {score, grade, type, breakdown}}."""
    results = {}

    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name in HUB_ONLY_SKILLS:
                continue
            s, bd = score_skill(skill_dir)
            results[skill_dir.name] = {
                "score": s, "grade": grade(s), "type": "skill", "breakdown": bd
            }

    if AGENTS_DIR.exists():
        for agent_path in sorted(AGENTS_DIR.glob("*.md")):
            if agent_path.name == "README.md" or agent_path.stem in HUB_ONLY_AGENTS:
                continue
            s, bd = score_agent(agent_path)
            results[agent_path.stem] = {
                "score": s, "grade": grade(s), "type": "agent", "breakdown": bd
            }

    if RULES_DIR.exists():
        for rule_path in sorted(RULES_DIR.glob("*.md")):
            if rule_path.name == "README.md" or rule_path.stem in HUB_ONLY_RULES:
                continue
            s, bd = score_rule(rule_path)
            results[rule_path.stem] = {
                "score": s, "grade": grade(s), "type": "rule", "breakdown": bd
            }

    return results


# ── Baseline Mode ─────────────────────────────────────────────────────────


def save_baseline(errors: list[str]) -> Path:
    """Save current violations as the baseline. Returns path to baseline file."""
    baseline = sorted(set(errors))
    BASELINE_PATH.write_text(
        json.dumps({"violations": baseline}, indent=2) + "\n",
        encoding="utf-8",
    )
    return BASELINE_PATH


def load_baseline() -> set[str]:
    """Load baseline violations. Returns empty set if no baseline exists."""
    if not BASELINE_PATH.exists():
        return set()
    try:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        return set(data.get("violations", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def filter_new_violations(errors: list[str], baseline: set[str]) -> list[str]:
    """Return only violations not in the baseline."""
    return [e for e in errors if e not in baseline]


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
    else:
        desc = str(fm["description"]).strip()
        desc_errors = check_description_quality(name, desc)
        errors.extend(desc_errors)

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
    parser.add_argument("--score", action="store_true",
                        help="Show quality scores (0-100) for all patterns")
    parser.add_argument("--baseline-save", action="store_true",
                        help="Save current violations as baseline for incremental adoption")
    parser.add_argument("--baseline", action="store_true",
                        help="Only report new violations not in the baseline")
    args = parser.parse_args()

    # Score mode
    if args.score:
        print("=" * 60)
        print("Pattern Quality Scores")
        print("=" * 60)

        results = score_all()
        by_grade = {"A": [], "B": [], "C": [], "D": [], "F": []}
        for name, data in results.items():
            by_grade[data["grade"]].append((name, data))

        total = len(results)
        for g in ["A", "B", "C", "D", "F"]:
            count = len(by_grade[g])
            if count == 0:
                continue
            print(f"\n{'-' * 40}")
            print(f"Grade {g}: {count} pattern(s)")
            print(f"{'-' * 40}")
            for name, data in sorted(by_grade[g], key=lambda x: -x[1]["score"]):
                print(f"  {data['score']:3d}/100 [{data['type']:6s}] {name}")
                if data["breakdown"] and data["score"] < 90:
                    for item in data["breakdown"]:
                        print(f"           {item}")

        avg = sum(d["score"] for d in results.values()) / total if total else 0
        grade_dist = {g: len(v) for g, v in by_grade.items() if v}
        print(f"\n{'=' * 60}")
        print(f"Total: {total} patterns | Average: {avg:.0f}/100 ({grade(int(avg))})")
        print(f"Distribution: {' | '.join(f'{g}:{c}' for g, c in grade_dist.items())}")
        below_b = len(by_grade["C"]) + len(by_grade["D"]) + len(by_grade["F"])
        if below_b:
            print(f"Action needed: {below_b} pattern(s) below Grade B (75)")
        print(f"{'=' * 60}")
        sys.exit(0)

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

    # Full validation mode
    print("=" * 60)
    print("Pattern Quality Validator")
    print("=" * 60)

    errors = validate_all()

    # Baseline save mode
    if args.baseline_save:
        path = save_baseline(errors)
        warnings = [e for e in errors if "WARNING" in e]
        hard_errors = [e for e in errors if "WARNING" not in e]
        print(f"\nBaseline saved to {path}")
        print(f"  {len(hard_errors)} error(s) and {len(warnings)} warning(s) baselined")
        print(f"  Future runs with --baseline will only report NEW violations")
        sys.exit(0)

    # Baseline filter mode
    if args.baseline:
        baseline = load_baseline()
        if not baseline:
            print("\nWARNING: No baseline found. Run --baseline-save first.")
            print("Falling back to full validation.\n")
        else:
            original_count = len(errors)
            errors = filter_new_violations(errors, baseline)
            suppressed = original_count - len(errors)
            if suppressed:
                print(f"\n  ({suppressed} baselined violation(s) suppressed)")

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
