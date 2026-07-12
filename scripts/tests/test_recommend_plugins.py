"""Plugin-recommendation layer of recommend.py (#187 install-not-copy end-state).

Pins: stack->pack mapping, dependency-trigger mapping (covers Vite+React projects the
stack detectors miss), universal set always present, graceful no-op when the config is
absent, and install-command formatting against the real shipped config.
"""

from pathlib import Path

from scripts.recommend import (
    load_plugin_recommendations,
    print_plugin_recommendations,
    recommend_plugins,
)

ROOT = Path(__file__).resolve().parent.parent.parent
REAL_CONFIG = ROOT / "config" / "plugin-recommendations.yml"

SAMPLE = {
    "marketplace": "claude-best-practices",
    "universal": [{"name": "cbp-workflows", "why": "review"}, {"name": "loop-engineering", "why": "loop"}],
    "by_stack": {"react-nextjs": ["cbp-react-stack"], "fastapi-python": ["cbp-python-stack"]},
    "by_dependency": {"vitest": ["cbp-react-stack"], "fastapi": ["cbp-python-stack"]},
    "provision_note": "rules stay provisioned",
}


def test_stack_maps_to_pack():
    rec = recommend_plugins(["react-nextjs"], {}, SAMPLE)
    assert rec["stack_packs"] == ["cbp-react-stack"]


def test_dependency_trigger_covers_undetected_stack():
    """A Vite+React app has no `next` dep, so no stack is detected — vitest must trigger."""
    rec = recommend_plugins([], {"npm": ["vitest", "react-dom"]}, SAMPLE)
    assert rec["stack_packs"] == ["cbp-react-stack"]


def test_stack_and_dep_dedupe():
    rec = recommend_plugins(["fastapi-python"], {"pip": ["fastapi"]}, SAMPLE)
    assert rec["stack_packs"] == ["cbp-python-stack"]


def test_universal_always_recommended():
    rec = recommend_plugins([], {}, SAMPLE)
    assert [u["name"] for u in rec["universal"]] == ["cbp-workflows", "loop-engineering"]
    assert rec["stack_packs"] == []


def test_install_commands_carry_marketplace_suffix():
    rec = recommend_plugins(["react-nextjs"], {}, SAMPLE)
    assert "/plugin install cbp-workflows@claude-best-practices" in rec["install_commands"]
    assert "/plugin install cbp-react-stack@claude-best-practices" in rec["install_commands"]


def test_absent_config_degrades_to_noop(tmp_path):
    cfg = load_plugin_recommendations(tmp_path / "missing.yml")
    assert cfg == {}
    assert recommend_plugins(["react-nextjs"], {}, cfg) == {}
    print_plugin_recommendations({})  # must not raise


def test_real_shipped_config_is_valid():
    cfg = load_plugin_recommendations(REAL_CONFIG)
    assert cfg.get("marketplace") == "claude-best-practices"
    names = [u["name"] for u in cfg["universal"]]
    assert "cbp-workflows" in names and "cbp-build-test-workflows" in names
    rec = recommend_plugins(["fastapi-python"], {"npm": ["react"]}, cfg)
    assert set(rec["stack_packs"]) == {"cbp-python-stack", "cbp-react-stack"}
    ROOT_MARKETPLACE = ROOT / "plugins" / ".claude-plugin" / "marketplace.json"
    import json
    registered = {p["name"] for p in json.loads(ROOT_MARKETPLACE.read_text(encoding="utf-8"))["plugins"]}
    for u in names + rec["stack_packs"]:
        if u.startswith("cbp-") or u in ("loop-engineering", "branch-lifecycle", "prompt-auto-enhance"):
            assert u in registered, f"recommended plugin {u} not registered in the marketplace"
