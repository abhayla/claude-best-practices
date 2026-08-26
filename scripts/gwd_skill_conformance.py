"""Reads .claude/skills/get-work-done/SKILL.md and the live fleet checkout
(GWD_ROOT) as fixtures for each other, per T-370's dod. Pure extraction/diff
functions — no test framework here so scripts/tests/test_gwd_skill_conformance.py
stays a thin assertion layer over these.
"""

import re
from pathlib import Path
from typing import Optional

import yaml

_SELF_SKILL_NAME = "get-work-done"


def load_skill_text(hub_root: Path) -> str:
    return (hub_root / ".claude" / "skills" / "get-work-done" / "SKILL.md").read_text(encoding="utf-8")


def load_grandfather(hub_root: Path) -> dict:
    path = hub_root / "config" / "gwd-skill-conformance-grandfather.yml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# --- (1) path / GWD\<script> references -------------------------------------------------

_GWD_TOKEN_RE = re.compile(r"GWD[\\/][^\s`)\]]+")
_ABS_TOKEN_RE = re.compile(r"D:\\Abhay\\[^\s`)\]]+")


def extract_path_refs(skill_text: str) -> list:
    """Every `GWD\\...` and `D:\\Abhay\\...` token named in the skill (dedup, sorted)."""
    tokens = set(_GWD_TOKEN_RE.findall(skill_text)) | set(_ABS_TOKEN_RE.findall(skill_text))
    return sorted(tokens)


def _resolve_dir_or_file(token: str, gwd_root: Path) -> tuple:
    """Returns (checked_path: Path, kind: 'file'|'dir')."""
    normalized = token.replace("\\", "/")
    if normalized.startswith("GWD/"):
        rel = normalized[len("GWD/"):]
        base = gwd_root
    elif normalized.startswith("D:/Abhay/"):
        rel = normalized[len("D:/Abhay/"):]
        base = Path("D:/Abhay")
    else:
        return None, None

    is_dir_hint = rel.endswith("/")
    if "<" in rel:
        prefix = rel[: rel.index("<")]
        rel = prefix.rsplit("/", 1)[0] if "/" in prefix else ""
        is_dir_hint = True
    if rel.endswith(".flag"):
        # a conditional runtime marker (present only while active) — check its
        # parent directory exists, not the flag file itself.
        rel = rel.rsplit("/", 1)[0] if "/" in rel else ""
        is_dir_hint = True
    rel = rel.rstrip("/")
    path = base / rel if rel else base
    return path, ("dir" if is_dir_hint else "file")


def missing_path_refs(skill_text: str, gwd_root: Path) -> list:
    """Path/script tokens the skill names that do not exist on disk."""
    missing = []
    for token in extract_path_refs(skill_text):
        path, kind = _resolve_dir_or_file(token, gwd_root)
        if path is None:
            continue
        if not path.exists():
            missing.append(token)
    return missing


# --- (2) settings.<key> references -------------------------------------------------------

_SETTINGS_KEY_RE = re.compile(r"settings\.([A-Za-z_][A-Za-z0-9_.]*)")


def extract_settings_keys(skill_text: str) -> list:
    keys = set()
    for m in _SETTINGS_KEY_RE.findall(skill_text):
        key = m.rstrip(".")
        if key == "json" or key.startswith("json."):
            continue  # "settings.json" = the file itself, not a key inside it
        keys.add(key)
    return sorted(keys)


def _flatten_keys(d: dict, prefix: str = "") -> set:
    keys = set()
    for k, v in d.items():
        p = f"{prefix}.{k}" if prefix else k
        keys.add(p)
        if isinstance(v, dict):
            keys |= _flatten_keys(v, p)
    return keys


def missing_settings_keys(skill_text: str, settings: dict) -> list:
    available = _flatten_keys(settings)
    return sorted(k for k in extract_settings_keys(skill_text) if k not in available)


# --- (3) preflight-guard.ps1 exit codes, bidirectional -----------------------------------

_SKILL_EXIT_RE = re.compile(r"\bexit\s+(\d+)\b", re.IGNORECASE)
_TABLE_CODE_RE = re.compile(r"^#\s+(\d{1,2})\s*=", re.MULTILINE)


def extract_skill_exit_codes(skill_text: str) -> set:
    return {int(n) for n in _SKILL_EXIT_RE.findall(skill_text)}


def extract_preflight_exit_codes(preflight_ps1_text: str) -> set:
    start = preflight_ps1_text.find("EXIT CODE TABLE")
    end = preflight_ps1_text.find("\nparam(", start if start >= 0 else 0)
    if start < 0:
        return set()
    table_block = preflight_ps1_text[start: end if end > start else None]
    return {int(n) for n in _TABLE_CODE_RE.findall(table_block)}


def exit_code_diff(skill_text: str, preflight_ps1_text: str) -> tuple:
    """Returns (codes_preflight_defines_skill_never_mentions, codes_skill_mentions_preflight_never_defines)."""
    skill_codes = extract_skill_exit_codes(skill_text)
    preflight_codes = extract_preflight_exit_codes(preflight_ps1_text)
    return (
        sorted(preflight_codes - skill_codes),
        sorted(skill_codes - preflight_codes),
    )


# --- (4) claude -p launch recipe count -----------------------------------------------------

_CLAUDE_P_RECIPE_RE = re.compile(r"claude -p [^\n]*--model")


def count_claude_p_recipes(skill_text: str) -> int:
    return len(_CLAUDE_P_RECIPE_RE.findall(skill_text))


# --- (5) /skill invocations resolve --------------------------------------------------------

_SKILL_REF_RE = re.compile(r"`/([a-zA-Z][a-zA-Z0-9-]*)`")


def extract_skill_invocations(skill_text: str) -> list:
    names = {m for m in _SKILL_REF_RE.findall(skill_text) if m != _SELF_SKILL_NAME}
    return sorted(names)


def unresolved_skill_invocations(skill_text: str, hub_root: Path, plugin_allowlist: Optional[list] = None) -> list:
    plugin_allowlist = plugin_allowlist or []
    allowed_by_plugin = {}
    for entry in plugin_allowlist:
        allowed_by_plugin[entry["skill"]] = hub_root / entry["path"]

    unresolved = []
    for name in extract_skill_invocations(skill_text):
        if (hub_root / ".claude" / "skills" / name).exists():
            continue
        plugin_path = allowed_by_plugin.get(name)
        if plugin_path is not None and plugin_path.exists():
            continue
        unresolved.append(name)
    return unresolved


# --- (6) byte-size ratchet -------------------------------------------------------------------

def skill_byte_size(hub_root: Path) -> int:
    return (hub_root / ".claude" / "skills" / "get-work-done" / "SKILL.md").stat().st_size


# --- CRITICAL RULES MUST<->gate manifest (T-370 dod item 3) ----------------------------------

_MUST_BULLET_RE = re.compile(r"^-\s+(MUST(?:\s+NOT)?\b.*)$", re.MULTILINE)
_GATE_TOKEN_RE = re.compile(r"gate:([A-Za-z0-9_-]+)")


def extract_critical_rules_block(skill_text: str) -> str:
    idx = skill_text.find("## CRITICAL RULES")
    if idx < 0:
        return ""
    return skill_text[idx:]


def extract_must_bullets(skill_text: str) -> list:
    """MUST/MUST NOT bullets in the CRITICAL RULES block (each bullet is the full
    multi-line text up to the next top-level `- ` bullet or a heading)."""
    block = extract_critical_rules_block(skill_text)
    lines = block.splitlines()
    bullets = []
    current = None
    for line in lines:
        if re.match(r"^-\s+MUST\b", line):
            if current is not None:
                bullets.append("\n".join(current))
            current = [line]
        elif current is not None:
            if line.startswith("## ") or (line.startswith("- ") and not line.startswith("  ")):
                bullets.append("\n".join(current))
                current = None
            else:
                current.append(line)
    if current is not None:
        bullets.append("\n".join(current))
    return bullets


def must_gate_tokens(skill_text: str) -> list:
    """One entry per MUST bullet: {'text': <first line>, 'gate': <id or None>}."""
    entries = []
    for bullet in extract_must_bullets(skill_text):
        m = _GATE_TOKEN_RE.search(bullet)
        entries.append({"text": bullet.splitlines()[0], "gate": m.group(1) if m else None})
    return entries


_LIST_FIELDS = ("missing_preflight_exit_codes", "stale_paths", "plugin_skill_allowlist")
_CEILING_FIELDS = ("max_bytes", "max_claude_p_recipes", "max_ungated_musts")


def _list_key(entry):
    """Comparable identity for a grandfather list entry (plain scalar or a {skill,path,...} dict)."""
    if isinstance(entry, dict):
        return (entry.get("skill"), entry.get("path"))
    return entry


def grandfather_shrink_violations(old: dict, new: dict) -> list:
    """Compare two loaded grandfather.yml dicts; return violation strings if `new` adds a
    list entry `old` never had, or raises a ceiling above `old`'s value. Removing entries
    or lowering ceilings is always allowed (that's the point of the ratchet)."""
    violations = []
    for field in _LIST_FIELDS:
        old_keys = {_list_key(e) for e in (old.get(field) or [])}
        new_keys = {_list_key(e) for e in (new.get(field) or [])}
        added = new_keys - old_keys
        if added:
            violations.append(f"{field}: new entries added {sorted(map(str, added))} — grandfather is shrink-only")
    for field in _CEILING_FIELDS:
        old_val, new_val = old.get(field), new.get(field)
        if old_val is not None and new_val is not None and new_val > old_val:
            violations.append(f"{field}: raised from {old_val} to {new_val} — grandfather is shrink-only")
    return violations


def load_gates(hub_root: Path) -> dict:
    path = hub_root / "config" / "gwd-gates.yml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("gates", {})
