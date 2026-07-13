"""The plugin version-bump CI gate (scripts/check_plugin_version_bump.py).

Pins, against real throwaway git repos: (1) source change without bump -> violation with
actionable message; (2) source change WITH bump -> clean; (3) README/evals-only changes
exempt; (4) brand-new plugin exempt; (5) the gate is wired into validate-pr.yml as a
blocking step.
"""

import json
import subprocess
import sys

import pytest

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GATE = ROOT / "scripts" / "check_plugin_version_bump.py"


def _repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    plug = r / "plugins" / "demo"
    (plug / ".claude-plugin").mkdir(parents=True)
    (plug / "skills" / "thing").mkdir(parents=True)
    (plug / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "demo", "version": "0.1.0"}), encoding="utf-8"
    )
    (plug / "skills" / "thing" / "SKILL.md").write_text("---\nname: thing\n---\nbody\n")
    (plug / "README.md").write_text("readme\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"],
                ["git", "branch", "-M", "main"]):
        subprocess.run(cmd, cwd=r, check=True)
    return r


def _run(repo: Path):
    return subprocess.run(
        [sys.executable, str(GATE), "--base", "main"],
        cwd=repo, capture_output=True, text=True,
    )


def _commit(repo: Path, msg: str):
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "checkout", "-qb", "work"], cwd=repo)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", msg], cwd=repo, check=True)


def test_source_change_without_bump_fails(tmp_path):
    r = _repo(tmp_path)
    (r / "plugins" / "demo" / "skills" / "thing" / "SKILL.md").write_text("changed\n")
    _commit(r, "edit skill, no bump")
    res = _run(r)
    assert res.returncode == 1
    assert "version-bump gate failed" in res.stdout.lower()
    assert "never reaches" in res.stdout.lower()


def test_source_change_with_bump_passes(tmp_path):
    r = _repo(tmp_path)
    (r / "plugins" / "demo" / "skills" / "thing" / "SKILL.md").write_text("changed\n")
    (r / "plugins" / "demo" / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "demo", "version": "0.1.1"}), encoding="utf-8"
    )
    _commit(r, "edit skill + bump")
    res = _run(r)
    assert res.returncode == 0, res.stdout


def test_readme_only_change_is_exempt(tmp_path):
    r = _repo(tmp_path)
    (r / "plugins" / "demo" / "README.md").write_text("better readme\n")
    _commit(r, "docs only")
    res = _run(r)
    assert res.returncode == 0, res.stdout


def test_new_plugin_is_exempt(tmp_path):
    r = _repo(tmp_path)
    newp = r / "plugins" / "fresh"
    (newp / ".claude-plugin").mkdir(parents=True)
    (newp / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "fresh", "version": "0.1.0"}), encoding="utf-8"
    )
    _commit(r, "new plugin")
    res = _run(r)
    assert res.returncode == 0, res.stdout


def test_gate_wired_into_validate_pr():
    wf = (ROOT / ".github" / "workflows" / "validate-pr.yml").read_text(encoding="utf-8")
    assert "check_plugin_version_bump.py" in wf, (
        "the version-bump gate must run in validate-pr.yml (blocking) — prose-only "
        "enforcement does not survive weaker models"
    )
