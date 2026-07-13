#!/usr/bin/env python3
"""BLOCKING CI gate: a plugin source change MUST bump that plugin's version.

WHY (the #1 propagation trap, /plugin-lifecycle cheat-sheet): Claude Code serves installed
plugins from a version-pinned cache (~/.claude/plugins/cache/<mkt>/<plugin>/<version>/).
A source edit that lands WITHOUT a version bump passes every other gate, merges green —
and silently never reaches any installed copy. Until 2026-07-13 this rule was prose-only
(model discipline); this gate makes it deterministic so it holds for ANY model driving a
session (owner question 2026-07-13: "how is the process followed when Fable5 is not
available?" — answer: in CI, not in the model).

Usage:
    PYTHONPATH=. python scripts/check_plugin_version_bump.py --base origin/main
    (wired into validate-pr.yml; exits 1 with an actionable message on violation)

Rules:
- For each plugin dir under plugins/ with changed files (vs --base), require that
  plugins/<name>/.claude-plugin/plugin.json's "version" differs from the base version.
- A brand-new plugin (no plugin.json at base) passes (its initial version is the bump).
- Changes ONLY to README.md or evals/ inside a plugin are exempt (docs don't need to
  reach the cache). Everything else — skills, hooks, agents, configs, plugin.json edits
  that don't touch version — requires the bump.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# cwd, not the script's location: CI runs the gate from the repo root, and tests run it
# against throwaway repos — pinning to __file__ would silently check the wrong repo.
REPO_ROOT = Path.cwd()
PLUGINS_DIR = "plugins"
EXEMPT_SUFFIXES = ("/README.md",)
EXEMPT_PARTS = ("/evals/",)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def changed_files(base: str) -> list[str]:
    out = _git("diff", "--name-only", f"{base}...HEAD")
    return [line.strip() for line in out.splitlines() if line.strip()]


def base_version(base: str, plugin: str) -> str | None:
    try:
        raw = _git("show", f"{base}:{PLUGINS_DIR}/{plugin}/.claude-plugin/plugin.json")
    except subprocess.CalledProcessError:
        return None  # plugin is new at HEAD
    try:
        return json.loads(raw).get("version")
    except json.JSONDecodeError:
        return None


def head_version(plugin: str) -> str | None:
    p = REPO_ROOT / PLUGINS_DIR / plugin / ".claude-plugin" / "plugin.json"
    if not p.exists():
        return None  # plugin deleted at HEAD — nothing to propagate
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("version")
    except json.JSONDecodeError:
        return None


def needs_bump(path: str) -> bool:
    if path.endswith(EXEMPT_SUFFIXES):
        return False
    return not any(part in path for part in EXEMPT_PARTS)


def check(base: str) -> list[str]:
    violations = []
    touched: dict[str, list[str]] = {}
    for f in changed_files(base):
        parts = f.split("/")
        if len(parts) >= 3 and parts[0] == PLUGINS_DIR and parts[1] != ".claude-plugin":
            if needs_bump(f):
                touched.setdefault(parts[1], []).append(f)
    for plugin, files in sorted(touched.items()):
        old = base_version(base, plugin)
        new = head_version(plugin)
        if old is None or new is None:
            continue  # new or deleted plugin — initial/removed version IS the change
        if old == new:
            violations.append(
                f"plugins/{plugin}: {len(files)} source file(s) changed but version is still "
                f"'{old}' — bump .claude-plugin/plugin.json version or the fix NEVER reaches "
                f"installed copies (version-pinned cache). First changed file: {files[0]}"
            )
    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main", help="git base ref to diff against")
    args = ap.parse_args()
    try:
        violations = check(args.base)
    except subprocess.CalledProcessError as e:
        print(f"check_plugin_version_bump: git diff against '{args.base}' failed: {e.stderr}")
        return 0  # fail-open on missing base (fresh clones); the PR context always has it
    if violations:
        print("PLUGIN VERSION-BUMP GATE FAILED:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("Plugin version-bump gate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
