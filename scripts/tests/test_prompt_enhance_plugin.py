"""Tests for the prompt-auto-enhance plugin (plugins/prompt-auto-enhance/).

Two layers:
  * Static — manifest + (plain-English) settings schema invariants (pure Python, always run).
  * Functional — the settings-driven hooks (skipped if bash/jq absent).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "prompt-auto-enhance"
MARKETPLACE = ROOT / "plugins" / ".claude-plugin" / "marketplace.json"
DEFAULTS = PLUGIN / "enhance-settings.default.json"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# ── Static: structure & manifests ──────────────────────────────────────────
def test_marketplace_lists_the_plugin():
    mk = _load(MARKETPLACE)
    entry = next(p for p in mk["plugins"] if p["name"] == "prompt-auto-enhance")
    assert entry["source"] == "./prompt-auto-enhance"


def test_plugin_manifest_valid():
    pj = _load(PLUGIN / ".claude-plugin" / "plugin.json")
    assert pj["name"] == "prompt-auto-enhance"
    assert pj["hooks"] == "./hooks/hooks.json"


def test_required_files_exist():
    for rel in [
        "enhance-settings.default.json", "prompt-auto-enhance-rule.md", "README.md",
        "hooks/hooks.json", "hooks/prompt-enhance-reminder.sh", "hooks/enhance-process-guard.sh",
        "commands/enhance-config.md", "skills/prompt-auto-enhance/SKILL.md",
    ]:
        assert (PLUGIN / rel).exists(), f"missing {rel}"


def test_hooks_json_wires_both_events():
    hj = _load(PLUGIN / "hooks" / "hooks.json")
    assert "UserPromptSubmit" in hj["hooks"] and "Stop" in hj["hooks"]


# ── Static: plain-English schema invariants ────────────────────────────────
def test_defaults_all_on():
    s = _load(DEFAULTS)
    assert s["enabled"] is True
    assert s["when_to_run"] == "automatic"
    assert s["after_improving"] == "run_immediately"
    assert s["enhance_slash_commands"] is False  # skip slash/custom prompts by default
    assert s["display"]["show_the_process"] is True
    assert s["display"]["how_much_to_show"] == "every_time"
    for k, v in s["display"]["show"].items():
        assert v is True, f"display.show.{k} should default ON"
    for k in ("skip_if_just_a_question", "skip_tip_for_simple_tasks",
              "also_check_when_short_prompt_makes_big_work"):
        assert s["when_to_enhance"][k] is True
    assert s["improving"]["always_add_a_role"] is True


def test_help_text_present():
    s = _load(DEFAULTS)
    assert "_help" in s and isinstance(s["_help"], dict) and len(s["_help"]) >= 15


def test_uses_plain_english_names():
    s = _load(DEFAULTS)
    for jargon in ("run_mode", "execute_mode", "render", "triggers", "enforce", "show",
                   "run", "grade", "clarify", "quality_checks", "context_levels"):
        assert jargon not in s, f"jargon key '{jargon}' should be renamed"
    for friendly in ("when_to_run", "after_improving", "display", "when_to_enhance",
                     "scoring_criteria", "ask_clarifying_questions", "background_research",
                     "make_sure_steps_were_shown", "enhance_slash_commands", "keep_a_quiet_log"):
        assert friendly in s, f"expected plain-English key '{friendly}'"


def test_role_always_added_no_threshold():
    s = _load(DEFAULTS)
    assert s["improving"]["always_add_a_role"] is True
    assert "add_role_when_score_below" not in s["improving"]  # removed per owner decision


def test_clarify_uses_grillme():
    assert _load(DEFAULTS)["ask_clarifying_questions"]["method"] == "grill-me"


def test_self_check_is_scoped_and_simple():
    s = _load(DEFAULTS)
    assert s["make_sure_steps_were_shown"] in ("strict", "relaxed", "off")
    assert s["background_research"] in ("light", "normal", "deep")
    assert "governance" not in s


def test_scoring_weights_sum_to_one():
    s = _load(DEFAULTS)
    total = sum(d["weight"] for d in s["scoring_criteria"])
    assert abs(total - 1.0) < 1e-9


# ── Functional: hooks ──────────────────────────────────────────────────────
_TOOLS = shutil.which("bash") and shutil.which("jq")
pytestmark_fn = pytest.mark.skipif(not _TOOLS, reason="bash + jq required for hook tests")

HOOK = PLUGIN / "hooks" / "prompt-enhance-reminder.sh"
GUARD = PLUGIN / "hooks" / "enhance-process-guard.sh"
_SUBSTANTIVE = "please refactor the authentication module thoroughly now"


def _run_hook(prompt: str, cwd: Path, settings_file: Path | None = None, home: Path | None = None) -> str:
    import os
    env = {**os.environ, "HOME": (home or cwd).as_posix()}
    if settings_file is not None:
        env["ENHANCE_SETTINGS_FILE"] = settings_file.as_posix()
    return subprocess.run(["bash", str(HOOK)], input=json.dumps({"prompt": prompt}),
                          capture_output=True, text=True, cwd=str(cwd), env=env).stdout


def _write_settings(tmp_path, **overrides):
    s = _load(DEFAULTS)
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
def test_short_prompt_skipped(tmp_path):
    assert _run_hook("hi there", tmp_path).strip() == ""


@pytestmark_fn
def test_substantive_prompt_emits_reminder(tmp_path):
    assert "REMINDER" in _run_hook(_SUBSTANTIVE, tmp_path)


@pytestmark_fn
def test_master_off_suppresses(tmp_path):
    sf = _write_settings(tmp_path, enabled=False)
    assert _run_hook(_SUBSTANTIVE, tmp_path, settings_file=sf).strip() == ""


@pytestmark_fn
def test_slash_command_skipped_by_default(tmp_path):
    # enhance_slash_commands defaults false → a /command runs as-is, even when long.
    assert _run_hook("/deploy the whole production stack to all regions now", tmp_path).strip() == ""


@pytestmark_fn
def test_slash_command_enhanced_when_opted_in(tmp_path):
    sf = _write_settings(tmp_path, enhance_slash_commands=True)
    assert "REMINDER" in _run_hook("/deploy the whole production stack to all regions now", tmp_path, settings_file=sf)


@pytestmark_fn
def test_skip_if_just_a_question_directive(tmp_path):
    assert "SKIP-IF-QUESTION" in _run_hook(_SUBSTANTIVE, tmp_path)


@pytestmark_fn
def test_always_role_directive(tmp_path):
    assert "ALWAYS-ROLE" in _run_hook(_SUBSTANTIVE, tmp_path)


@pytestmark_fn
def test_clarify_directive_names_grillme(tmp_path):
    assert "grill-me" in _run_hook(_SUBSTANTIVE, tmp_path).lower()


@pytestmark_fn
def test_second_opinion_off_drops_column(tmp_path):
    sf = _write_settings(tmp_path, **{"display.show.second_opinion_review": False})
    out = _run_hook(_SUBSTANTIVE, tmp_path, settings_file=sf)
    assert "REMINDER" in out and "Reviewer-after" not in out


@pytestmark_fn
@pytest.mark.parametrize("mode,needle", [("ask_first", "ask"), ("off", "directly")])
def test_when_to_run_branches(tmp_path, mode, needle):
    sf = _write_settings(tmp_path, when_to_run=mode)
    assert needle in _run_hook(_SUBSTANTIVE, tmp_path, settings_file=sf).lower()


@pytestmark_fn
def test_display_off_is_silent(tmp_path):
    sf = _write_settings(tmp_path, **{"display.show_the_process": False})
    out = _run_hook(_SUBSTANTIVE, tmp_path, settings_file=sf).lower()
    assert "internally" in out and "only the answer" in out


@pytestmark_fn
def test_review_first(tmp_path):
    sf = _write_settings(tmp_path, after_improving="let_me_review_first")
    out = _run_hook(_SUBSTANTIVE, tmp_path, settings_file=sf).lower()
    assert "let_me_review_first" in out and "stop" in out


@pytestmark_fn
@pytest.mark.parametrize("mode", ["only_for_weak_prompts", "scale_to_prompt_quality"])
def test_display_condition_emitted(tmp_path, mode):
    sf = _write_settings(tmp_path, **{"display.how_much_to_show": mode})
    assert "DISPLAY CONDITION" in _run_hook(_SUBSTANTIVE, tmp_path, settings_file=sf)


@pytestmark_fn
def test_global_config_applies_to_a_project(tmp_path):
    home, proj = tmp_path / "home", tmp_path / "proj"
    proj.mkdir()
    cfg = home / ".claude" / "enhance-settings.json"
    cfg.parent.mkdir(parents=True)
    s = _load(DEFAULTS); s["enabled"] = False
    cfg.write_text(json.dumps(s), encoding="utf-8")
    assert _run_hook(_SUBSTANTIVE, proj, home=home).strip() == ""


# ── Functional: Stop-hook enforcement ──────────────────────────────────────
_LONG = "This is a substantive working turn that does real analysis. " * 8


def _run_stop(assistant_text: str, tmp_path: Path, settings_file: Path | None = None) -> str:
    import os
    tp = tmp_path / "transcript.jsonl"
    lines = [
        {"type": "user", "message": {"content": "please do a substantial task now"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": assistant_text}]}},
    ]
    tp.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    env = {**os.environ, "HOME": tmp_path.as_posix()}
    if settings_file is not None:
        env["ENHANCE_SETTINGS_FILE"] = settings_file.as_posix()
    return subprocess.run(["bash", str(GUARD)], input=json.dumps({"transcript_path": tp.as_posix()}),
                          capture_output=True, text=True, cwd=str(tmp_path), env=env).stdout


@pytestmark_fn
def test_stop_blocks_when_table_missing(tmp_path):
    assert '"block"' in _run_stop(_LONG + " no table here at all.", tmp_path)


@pytestmark_fn
def test_stop_passes_with_full_process(tmp_path):
    text = _LONG + " Diagnosis: VAGUE_INTENT. Reviewer-after column present. Changes Applied: [1] fix."
    assert _run_stop(text, tmp_path).strip() == ""


@pytestmark_fn
def test_stop_suppressed_when_self_check_off(tmp_path):
    sf = _write_settings(tmp_path, make_sure_steps_were_shown="off")
    assert _run_stop(_LONG + " no table.", tmp_path, settings_file=sf).strip() == ""


@pytestmark_fn
def test_stop_no_block_when_review_off(tmp_path):
    sf = _write_settings(tmp_path, **{"display.show.second_opinion_review": False})
    text = _LONG + " Diagnosis: MISSING_CONTEXT. Changes Applied: [1] fix."
    assert _run_stop(text, tmp_path, settings_file=sf).strip() == ""


@pytestmark_fn
@pytest.mark.parametrize("mode", ["only_for_weak_prompts", "scale_to_prompt_quality"])
def test_stop_no_block_in_adaptive_modes(tmp_path, mode):
    sf = _write_settings(tmp_path, **{"display.how_much_to_show": mode})
    assert _run_stop(_LONG + " one-liner, no table.", tmp_path, settings_file=sf).strip() == ""
