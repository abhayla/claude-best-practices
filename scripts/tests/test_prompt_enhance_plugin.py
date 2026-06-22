"""Tests for the prompt-auto-enhance plugin (plugins/prompt-auto-enhance/).

Two layers:
  * Static — manifest + settings schema invariants (pure Python, always run).
  * Functional — the settings-driven UserPromptSubmit hook gating (skipped if bash/jq absent).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "prompt-auto-enhance"
MARKETPLACE = ROOT / "plugins" / ".claude-plugin" / "marketplace.json"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# ── Static: structure & manifests ──────────────────────────────────────────
def test_marketplace_lists_the_plugin():
    mk = _load(MARKETPLACE)
    names = [p["name"] for p in mk["plugins"]]
    assert "prompt-auto-enhance" in names
    entry = next(p for p in mk["plugins"] if p["name"] == "prompt-auto-enhance")
    assert entry["source"] == "./prompt-auto-enhance"


def test_plugin_manifest_valid():
    pj = _load(PLUGIN / ".claude-plugin" / "plugin.json")
    assert pj["name"] == "prompt-auto-enhance"
    assert pj["hooks"] == "./hooks/hooks.json"


def test_required_files_exist():
    for rel in [
        "enhance-settings.default.json",
        "prompt-auto-enhance-rule.md",
        "README.md",
        "hooks/hooks.json",
        "hooks/prompt-enhance-reminder.sh",
        "hooks/enhance-process-guard.sh",
        "commands/enhance-config.md",
        "skills/prompt-auto-enhance/SKILL.md",
    ]:
        assert (PLUGIN / rel).exists(), f"missing {rel}"


def test_hooks_json_wires_both_events():
    hj = _load(PLUGIN / "hooks" / "hooks.json")
    assert "UserPromptSubmit" in hj["hooks"]
    assert "Stop" in hj["hooks"]


# ── Static: settings schema — every criterion present and default ON ────────
def test_defaults_all_on():
    s = _load(PLUGIN / "enhance-settings.default.json")
    assert s["enabled"] is True
    assert s["run_mode"] == "auto"
    for k, v in s["show"].items():
        assert v is True, f"show.{k} should default ON"
    assert s["run"]["independent_reviewer"] is True
    assert s["triggers"]["length_gate"]["on"] is True
    assert s["triggers"]["length_gate"]["unit"] == "words"
    assert s["clarify"]["on"] is True


def test_grade_weights_sum_to_one():
    s = _load(PLUGIN / "enhance-settings.default.json")
    total = sum(d["weight"] for d in s["grade"]["dimensions"])
    assert abs(total - 1.0) < 1e-9, f"grade weights sum to {total}, expected 1.0"


def test_enforce_is_enhance_scoped_only():
    """Plugin ships ONLY prompt-auto-enhance self-governance — NOT hub-wide governance."""
    s = _load(PLUGIN / "enhance-settings.default.json")
    assert set(s["enforce"]) <= {"reviewer_card", "diagnosis_substance", "telemetry"}
    # Hub-wide governance must NOT be packaged in this plugin.
    assert "governance" not in s
    for banned in ("over_ask", "narrate_and_stop", "keepgoing_cap"):
        assert banned not in s["enforce"], f"hub-governance key {banned} must not ship"


# ── Functional: the trigger/verbosity hook ─────────────────────────────────
_TOOLS = shutil.which("bash") and shutil.which("jq")
pytestmark_fn = pytest.mark.skipif(not _TOOLS, reason="bash + jq required for hook tests")

HOOK = PLUGIN / "hooks" / "prompt-enhance-reminder.sh"


def _run_hook(prompt: str, cwd: Path, settings_file: Path | None = None) -> str:
    payload = json.dumps({"prompt": prompt})
    env = None
    if settings_file is not None:
        import os
        # Git Bash accepts forward-slash paths (C:/...); backslashes break the -f test.
        env = {**os.environ, "ENHANCE_SETTINGS_FILE": settings_file.as_posix()}
    res = subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, cwd=str(cwd), env=env,
    )
    return res.stdout


@pytestmark_fn
def test_short_prompt_skipped(tmp_path):
    # 2 words < default min 4 → length gate skips → no reminder.
    assert _run_hook("hi there", tmp_path).strip() == ""


@pytestmark_fn
def test_substantive_prompt_emits_reminder(tmp_path):
    out = _run_hook("please refactor the authentication module thoroughly now", tmp_path)
    assert "REMINDER" in out


@pytestmark_fn
def test_master_off_override_suppresses(tmp_path):
    # A project override with enabled=false must suppress even a substantive prompt.
    cfg = tmp_path / ".claude"
    cfg.mkdir()
    settings = _load(PLUGIN / "enhance-settings.default.json")
    settings["enabled"] = False
    sf = cfg / "enhance-settings.json"
    sf.write_text(json.dumps(settings), encoding="utf-8")
    out = _run_hook("please refactor the authentication module thoroughly now", tmp_path, settings_file=sf)
    assert out.strip() == ""


@pytestmark_fn
def test_emitted_components_follow_show_toggles(tmp_path):
    # Turn off the reviewer column in an override → reminder must not request it.
    cfg = tmp_path / ".claude"
    cfg.mkdir()
    settings = _load(PLUGIN / "enhance-settings.default.json")
    settings["show"]["reviewer_column"] = False
    sf = cfg / "enhance-settings.json"
    sf.write_text(json.dumps(settings), encoding="utf-8")
    out = _run_hook("please refactor the authentication module thoroughly now", tmp_path, settings_file=sf)
    assert "REMINDER" in out
    assert "Reviewer-after" not in out


def _write_settings(tmp_path, **overrides):
    s = _load(PLUGIN / "enhance-settings.default.json")
    for dotted, val in overrides.items():
        node = s
        keys = dotted.split(".")
        for k in keys[:-1]:
            node = node[k]
        node[keys[-1]] = val
    sf = tmp_path / "s.json"
    sf.write_text(json.dumps(s), encoding="utf-8")
    return sf


@pytestmark_fn
def test_reviewer_off_drops_column_request(tmp_path):
    # run.independent_reviewer off must remove the column request even if show.reviewer_column on.
    sf = _write_settings(tmp_path, **{"run.independent_reviewer": False})
    out = _run_hook("please refactor the authentication module thoroughly now", tmp_path, settings_file=sf)
    assert "REMINDER" in out
    assert "Reviewer-after" not in out


@pytestmark_fn
@pytest.mark.parametrize("mode,needle", [("silent", "silent"), ("ask", "ask"), ("off", "directly")])
def test_run_mode_branches(tmp_path, mode, needle):
    sf = _write_settings(tmp_path, run_mode=mode)
    out = _run_hook("please refactor the authentication module thoroughly now", tmp_path, settings_file=sf)
    assert needle in out.lower()


# ── Functional: the Stop-hook enforcement (enhance-process-guard.sh) ────────
GUARD = PLUGIN / "hooks" / "enhance-process-guard.sh"
_LONG = "This is a substantive working turn that does real analysis. " * 8  # > 300 chars


def _run_stop(assistant_text: str, tmp_path: Path, settings_file: Path | None = None) -> str:
    tp = tmp_path / "transcript.jsonl"
    lines = [
        {"type": "user", "message": {"content": "please do a substantial task now"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": assistant_text}]}},
    ]
    tp.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    payload = json.dumps({"transcript_path": tp.as_posix()})
    env = None
    if settings_file is not None:
        import os
        env = {**os.environ, "ENHANCE_SETTINGS_FILE": settings_file.as_posix()}
    res = subprocess.run(
        ["bash", str(GUARD)], input=payload, capture_output=True, text=True, cwd=str(tmp_path), env=env
    )
    return res.stdout


@pytestmark_fn
def test_stop_blocks_when_card_missing(tmp_path):
    out = _run_stop(_LONG + " no card here at all.", tmp_path)
    assert '"block"' in out


@pytestmark_fn
def test_stop_passes_with_full_process(tmp_path):
    text = _LONG + " Diagnosis: VAGUE_INTENT. Reviewer-after column present. Changes Applied: [1] fix."
    assert _run_stop(text, tmp_path).strip() == ""


@pytestmark_fn
def test_stop_suppressed_when_disabled(tmp_path):
    sf = _write_settings(tmp_path, enabled=False)
    assert _run_stop(_LONG + " no card.", tmp_path, settings_file=sf).strip() == ""


@pytestmark_fn
def test_stop_no_block_when_reviewer_off(tmp_path):
    # Reviewer off → missing card must NOT block (but substance still required).
    sf = _write_settings(tmp_path, **{"run.independent_reviewer": False})
    text = _LONG + " Diagnosis: MISSING_CONTEXT. Changes Applied: [1] fix."
    assert _run_stop(text, tmp_path, settings_file=sf).strip() == ""
