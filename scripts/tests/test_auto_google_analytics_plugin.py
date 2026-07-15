"""Gates for the auto-google-analytics plugin (added by the 2026-07-15 skill-evaluator fix batch).

1. Drift gate: analytics-setup ships BOTH as a core distributable and bundled inside the
   plugin (it is NOT covered by config/dual-home-resources.yml, which only pairs .claude/
   with core/.claude/). The two copies must stay byte-identical or the hub distributes a
   different engine than the plugin installs.
2. verify_hit.record_verdict: --audit reports the "last_verify" verdict per origin, so the
   verify script must actually persist it (eval finding S4: the claim existed with no writer).
"""

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "auto-google-analytics"
CORE_ENGINE = REPO / "core" / ".claude" / "skills" / "analytics-setup"
PLUGIN_ENGINE = PLUGIN / "skills" / "analytics-setup"


def _load_verify_hit():
    spec = importlib.util.spec_from_file_location(
        "aga_verify_hit", PLUGIN / "scripts" / "verify_hit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAnalyticsSetupDualCopySync:
    def test_skill_md_byte_identical(self):
        core = (CORE_ENGINE / "SKILL.md").read_bytes()
        plug = (PLUGIN_ENGINE / "SKILL.md").read_bytes()
        assert core == plug, (
            "core/.claude/skills/analytics-setup/SKILL.md has drifted from the copy bundled "
            "in plugins/auto-google-analytics — apply the same edit to BOTH (plugin-lifecycle "
            "STEP 4) so the hub distributes what the plugin installs.")

    def test_cross_platform_reference_byte_identical(self):
        core = (CORE_ENGINE / "references" / "cross-platform.md").read_bytes()
        plug = (PLUGIN_ENGINE / "references" / "cross-platform.md").read_bytes()
        assert core == plug, (
            "references/cross-platform.md has drifted between core and the "
            "auto-google-analytics plugin bundle — sync both copies in the same change.")


class TestRecordVerdict:
    def _inventory(self, tmp_path, sites):
        p = tmp_path / "analytics-inventory.json"
        p.write_text(json.dumps({"sites": sites}), encoding="utf-8")
        return p

    def test_writes_last_verify_for_origin(self, tmp_path):
        vh = _load_verify_hit()
        inv = self._inventory(tmp_path, {
            "https://example.com": {"property": "properties/1", "stream": "s", "measurement_id": "G-X"}})
        vh.record_verdict(str(inv), "https://example.com", "VERIFIED")
        data = json.loads(inv.read_text(encoding="utf-8"))
        lv = data["sites"]["https://example.com"]["last_verify"]
        assert lv["verdict"] == "VERIFIED"
        assert lv["event"] == vh.EVENT
        assert "ts" in lv

    def test_not_seen_verdict_persisted(self, tmp_path):
        vh = _load_verify_hit()
        inv = self._inventory(tmp_path, {
            "https://example.com": {"property": "properties/1", "stream": "s", "measurement_id": "G-X"}})
        vh.record_verdict(str(inv), "https://example.com", "NOT_SEEN")
        data = json.loads(inv.read_text(encoding="utf-8"))
        assert data["sites"]["https://example.com"]["last_verify"]["verdict"] == "NOT_SEEN"

    def test_missing_file_is_noop(self, tmp_path):
        vh = _load_verify_hit()
        vh.record_verdict(str(tmp_path / "absent.json"), "https://example.com", "VERIFIED")

    def test_unknown_origin_leaves_inventory_untouched(self, tmp_path):
        vh = _load_verify_hit()
        inv = self._inventory(tmp_path, {
            "https://example.com": {"property": "properties/1", "stream": "s", "measurement_id": "G-X"}})
        before = inv.read_text(encoding="utf-8")
        vh.record_verdict(str(inv), "https://other.com", "VERIFIED")
        assert inv.read_text(encoding="utf-8") == before

    def test_empty_args_are_noop(self, tmp_path):
        vh = _load_verify_hit()
        vh.record_verdict("", "https://example.com", "VERIFIED")
        vh.record_verdict(str(tmp_path / "x.json"), "", "VERIFIED")


class TestOrchestratorSkillFallbackTarget:
    def test_guided_manual_fallback_points_at_injection_not_provisioning(self):
        """Eval finding S2 (CRITICAL): the no-key fallback used to say 'skip to STEP 3'
        (provisioning), which hard-fails without the key. It must point at STEP 4."""
        text = (PLUGIN / "skills" / "auto-google-analytics" / "SKILL.md").read_text(encoding="utf-8")
        assert "skip to STEP 3" not in text
        assert "skip to STEP 4" in text
