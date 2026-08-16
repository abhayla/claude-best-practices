"""The root-marketplace generator (scripts/generate_root_marketplace.py).

Pins: (1) generated sources are rewritten to ./plugins/<name> so a GitHub-URL-cloned
marketplace resolves them; (2) --check passes when in sync, fails when stale/missing;
(3) the real repo's root marketplace.json is actually in sync (catches drift landing
without regenerating); (4) the check is wired into validate-pr.yml as a blocking step.
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "generate_root_marketplace.py"


def _load_module(monkeypatch, source_path: Path, root_path: Path):
    spec = importlib.util.spec_from_file_location("generate_root_marketplace_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "SOURCE_MARKETPLACE_PATH", source_path)
    monkeypatch.setattr(mod, "ROOT_MARKETPLACE_PATH", root_path)
    return mod


def _write_source(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "name": "demo-hub",
        "owner": {"name": "t"},
        "metadata": {"description": "d", "version": "0.1.0"},
        "plugins": [
            {"name": "alpha", "source": "./alpha", "description": "a"},
            {"name": "beta", "source": "./beta", "description": "b"},
        ],
    }), encoding="utf-8")


def test_derive_rewrites_sources_to_plugins_prefix(monkeypatch, tmp_path):
    src = tmp_path / "plugins" / ".claude-plugin" / "marketplace.json"
    dst = tmp_path / ".claude-plugin" / "marketplace.json"
    _write_source(src)
    mod = _load_module(monkeypatch, src, dst)

    with open(src, encoding="utf-8") as f:
        source = json.load(f)
    derived = mod.derive_root_marketplace(source)

    sources = {p["name"]: p["source"] for p in derived["plugins"]}
    assert sources == {"alpha": "./plugins/alpha", "beta": "./plugins/beta"}
    assert "_generated" in derived["metadata"]


def test_check_fails_when_missing(monkeypatch, tmp_path, capsys):
    src = tmp_path / "plugins" / ".claude-plugin" / "marketplace.json"
    dst = tmp_path / ".claude-plugin" / "marketplace.json"
    _write_source(src)
    mod = _load_module(monkeypatch, src, dst)

    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--check"])
    rc = mod.main()
    assert rc == 1
    assert "STALE" in capsys.readouterr().err


def test_check_passes_after_generate(monkeypatch, tmp_path, capsys):
    src = tmp_path / "plugins" / ".claude-plugin" / "marketplace.json"
    dst = tmp_path / ".claude-plugin" / "marketplace.json"
    _write_source(src)
    mod = _load_module(monkeypatch, src, dst)

    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    assert mod.main() == 0

    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--check"])
    assert mod.main() == 0


def test_check_fails_when_stale(monkeypatch, tmp_path):
    src = tmp_path / "plugins" / ".claude-plugin" / "marketplace.json"
    dst = tmp_path / ".claude-plugin" / "marketplace.json"
    _write_source(src)
    mod = _load_module(monkeypatch, src, dst)

    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    mod.main()

    # Source changes (new plugin added) without regenerating the root mirror.
    with open(src, encoding="utf-8") as f:
        source = json.load(f)
    source["plugins"].append({"name": "gamma", "source": "./gamma", "description": "g"})
    src.write_text(json.dumps(source), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--check"])
    assert mod.main() == 1


def test_real_repo_root_marketplace_is_in_sync():
    """Catches drift: a plugin registered/renamed in the source file without regenerating."""
    spec = importlib.util.spec_from_file_location("generate_root_marketplace_real", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with open(mod.SOURCE_MARKETPLACE_PATH, encoding="utf-8") as f:
        source = json.load(f)
    expected = mod.render(mod.derive_root_marketplace(source))

    assert mod.ROOT_MARKETPLACE_PATH.is_file(), (
        "root .claude-plugin/marketplace.json is missing — run "
        "scripts/generate_root_marketplace.py"
    )
    actual = mod.ROOT_MARKETPLACE_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "root .claude-plugin/marketplace.json is stale — run "
        "scripts/generate_root_marketplace.py"
    )


def test_gate_wired_into_validate_pr():
    wf = (ROOT / ".github" / "workflows" / "validate-pr.yml").read_text(encoding="utf-8")
    assert "generate_root_marketplace.py --check" in wf, (
        "the root-marketplace sync check must run in validate-pr.yml (blocking) — "
        "otherwise the root mirror silently drifts from the source marketplace.json"
    )
