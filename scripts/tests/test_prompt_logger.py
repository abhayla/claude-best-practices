"""Tests for the prompt-logger UserPromptSubmit hook.

The hook appends every user prompt to `.claude/tasks/prompts.md` in the repo root.
It MUST be non-blocking (exit 0 under every failure mode) and MUST NOT write to
stdout — on UserPromptSubmit events, stdout is injected into the conversation
context, which would double every prompt's cost.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
CORE_HOOK = REPO_ROOT / "core" / ".claude" / "hooks" / "prompt-logger.sh"
HUB_HOOK = REPO_ROOT / ".claude" / "hooks" / "prompt-logger.sh"


def _have(binary: str) -> bool:
    return shutil.which(binary) is not None


jq_required = pytest.mark.skipif(not _have("jq"), reason="jq not installed")
git_required = pytest.mark.skipif(not _have("git"), reason="git not installed")


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with `.claude/tasks/` pre-created."""
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / ".claude" / "tasks").mkdir(parents=True)
    return tmp_path


def _run(hook: Path, repo: Path, payload: dict | str) -> subprocess.CompletedProcess:
    stdin = json.dumps(payload) if isinstance(payload, dict) else payload
    return subprocess.run(
        ["bash", str(hook)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=repo,
    )


def _log(repo: Path) -> Path:
    return repo / ".claude" / "tasks" / "prompts.md"


# --- structural -----------------------------------------------------------


def test_core_hook_exists_and_is_readable():
    assert CORE_HOOK.exists(), f"missing {CORE_HOOK}"
    assert CORE_HOOK.read_text().startswith("#!"), "hook must have a shebang"


def test_hub_hook_exists_and_matches_core_byte_for_byte():
    assert HUB_HOOK.exists(), f"missing {HUB_HOOK}"
    assert HUB_HOOK.read_bytes() == CORE_HOOK.read_bytes(), (
        "hub and core hooks must be identical — sync_to_projects.py treats core/ as SSOT"
    )


def test_core_seed_exists_and_is_header_only():
    seed = REPO_ROOT / "core" / ".claude" / "tasks" / "prompts.md"
    assert seed.exists(), f"missing {seed}"
    content = seed.read_text()
    assert "# Prompt Log" in content
    assert "## " not in content, "seed must not contain any entry headings"


def test_hub_live_log_exists_with_header():
    log = REPO_ROOT / ".claude" / "tasks" / "prompts.md"
    assert log.exists(), f"missing {log}"
    assert "# Prompt Log" in log.read_text()


def test_gitignore_excludes_live_log():
    gi = (REPO_ROOT / ".gitignore").read_text()
    assert "/.claude/tasks/prompts.md" in gi, (
        "live prompt log must be gitignored — it may contain secrets"
    )


def test_settings_json_wires_prompt_logger_hook():
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
    ups = settings["hooks"]["UserPromptSubmit"]
    commands = [h["command"] for entry in ups for h in entry["hooks"]]
    assert any("prompt-logger.sh" in c for c in commands), (
        "settings.json must include a UserPromptSubmit hook for prompt-logger.sh"
    )


# --- behavioural ----------------------------------------------------------


@jq_required
@git_required
def test_appends_entry_with_required_fields(tmp_repo):
    r = _run(CORE_HOOK, tmp_repo, {"prompt": "Hello world", "session_id": "abc123", "cwd": str(tmp_repo)})
    assert r.returncode == 0
    content = _log(tmp_repo).read_text()
    assert "## " in content        # heading
    assert "abc123" in content     # session id
    assert "Hello world" in content


@jq_required
@git_required
def test_stdout_is_silent(tmp_repo):
    # UserPromptSubmit stdout gets injected into the conversation — hook MUST stay quiet.
    r = _run(CORE_HOOK, tmp_repo, {"prompt": "silent test", "session_id": "s", "cwd": str(tmp_repo)})
    assert r.stdout == "", f"hook wrote to stdout: {r.stdout!r}"


@jq_required
@git_required
def test_multiple_appends_do_not_clobber(tmp_repo):
    _run(CORE_HOOK, tmp_repo, {"prompt": "FIRST", "session_id": "s", "cwd": str(tmp_repo)})
    _run(CORE_HOOK, tmp_repo, {"prompt": "SECOND", "session_id": "s", "cwd": str(tmp_repo)})
    content = _log(tmp_repo).read_text()
    assert content.count("FIRST") == 1
    assert content.count("SECOND") == 1
    assert content.count("\n## ") >= 2, "each entry gets its own heading"


@jq_required
@git_required
def test_uses_tilde_fence_for_triple_backtick_survival(tmp_repo):
    prompt = "```python\nprint('x')\n```"
    _run(CORE_HOOK, tmp_repo, {"prompt": prompt, "session_id": "s", "cwd": str(tmp_repo)})
    content = _log(tmp_repo).read_text()
    assert "print('x')" in content, "raw prompt body preserved verbatim"
    assert "~~~" in content, "wrapping fence must be triple-tilde, not triple-backtick"


@jq_required
@git_required
def test_nonblocking_on_malformed_stdin(tmp_repo):
    r = _run(CORE_HOOK, tmp_repo, "this is not JSON")
    assert r.returncode == 0
    # No entry should be appended for malformed input.
    if _log(tmp_repo).exists():
        assert "## " not in _log(tmp_repo).read_text()


@jq_required
@git_required
def test_skips_empty_prompt(tmp_repo):
    r = _run(CORE_HOOK, tmp_repo, {"prompt": "", "session_id": "s", "cwd": str(tmp_repo)})
    assert r.returncode == 0
    if _log(tmp_repo).exists():
        assert "## " not in _log(tmp_repo).read_text()


@jq_required
@git_required
def test_includes_git_branch_and_short_sha(tmp_repo):
    (tmp_repo / "x.txt").write_text("hi")
    subprocess.run(["git", "add", "."], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_repo, check=True)
    _run(CORE_HOOK, tmp_repo, {"prompt": "with git", "session_id": "s", "cwd": str(tmp_repo)})
    content = _log(tmp_repo).read_text()
    assert re.search(r"main@[0-9a-f]{7,}", content), (
        "heading should include branch@shortsha when git is available"
    )


@jq_required
@git_required
def test_creates_header_when_log_missing(tmp_repo):
    log = _log(tmp_repo)
    assert not log.exists()
    _run(CORE_HOOK, tmp_repo, {"prompt": "first ever", "session_id": "s", "cwd": str(tmp_repo)})
    assert log.exists()
    assert "# Prompt Log" in log.read_text()


@jq_required
@git_required
def test_preserves_newlines_in_prompt(tmp_repo):
    prompt = "line one\nline two\nline three"
    _run(CORE_HOOK, tmp_repo, {"prompt": prompt, "session_id": "s", "cwd": str(tmp_repo)})
    content = _log(tmp_repo).read_text()
    assert "line one\nline two\nline three" in content


@jq_required
@git_required
def test_iso_utc_timestamp_in_heading(tmp_repo):
    _run(CORE_HOOK, tmp_repo, {"prompt": "ts check", "session_id": "s", "cwd": str(tmp_repo)})
    content = _log(tmp_repo).read_text()
    assert re.search(r"## \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", content), (
        "heading timestamp must be ISO-8601 UTC with seconds precision"
    )
