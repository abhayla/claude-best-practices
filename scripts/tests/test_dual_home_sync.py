"""CI gate for dual-home resources (.claude/ <-> core/.claude/).

Enforces config/dual-home-resources.yml against reality:
- every resource present in BOTH trees is classified (synced | divergent) — no silent drift,
- every `synced` pair is normalized-identical (a change to one side must be mirrored),
- the manifest has no stale entries (names that aren't actually dual-home) and no double-classification.

Reconcile a drifted synced pair with:
    python scripts/sync_dual_home.py --sync <name> --from hub|core
"""

import pytest

from scripts import sync_dual_home as s


@pytest.fixture(scope="module")
def report():
    return s.check()


@pytest.fixture(scope="module")
def manifest():
    return s.load_manifest()


def test_every_dual_home_resource_is_classified(report):
    unclassified = [f"{r['kind']}/{r['name']}" for r in report["unclassified"]]
    assert unclassified == [], (
        "Unclassified dual-home resources (in both .claude/ and core/.claude/ but not in the "
        "manifest). Add each to config/dual-home-resources.yml as synced or divergent: "
        f"{unclassified}"
    )


def test_synced_resources_are_identical(report):
    drifted = [f"{r['kind']}/{r['name']}" for r in report["drifted"]]
    assert drifted == [], (
        "These are declared `synced` but the hub and core copies have DRIFTED. Reconcile with "
        "`python scripts/sync_dual_home.py --sync <name> --from hub|core`: " + str(drifted)
    )


def test_manifest_has_no_stale_entries(manifest):
    """Every name in the manifest must be a real dual-home resource (present in both trees)."""
    real = {(r["kind"], r["name"]) for r in s.discover()}
    stale = []
    for cls in ("synced", "divergent"):
        for kind, entries in (manifest.get(cls, {}) or {}).items():
            names = entries.keys() if isinstance(entries, dict) else (entries or [])
            for name in names:
                if (kind, name) not in real:
                    stale.append(f"{cls}:{kind}/{name}")
    assert stale == [], f"Manifest lists resources that are not dual-home (remove them): {stale}"


def test_no_resource_classified_twice(manifest):
    synced = {(k, n) for k, lst in (manifest.get("synced", {}) or {}).items() for n in (lst or [])}
    divergent = {(k, n) for k, d in (manifest.get("divergent", {}) or {}).items() for n in (d or {})}
    overlap = synced & divergent
    assert not overlap, f"Resources classified as BOTH synced and divergent: {sorted(overlap)}"


def test_divergent_entries_have_a_reason(manifest):
    missing = [
        f"{kind}/{name}"
        for kind, d in (manifest.get("divergent", {}) or {}).items()
        for name, reason in (d or {}).items()
        if not (reason and str(reason).strip())
    ]
    assert missing == [], f"`divergent` entries must carry a reason: {missing}"


def test_in_sync_helper_detects_difference(tmp_path):
    """Sanity: the normalized comparison flags a real content difference (not just whitespace)."""
    a = tmp_path / "a.md"; b = tmp_path / "b.md"; c = tmp_path / "c.md"
    a.write_text("line one\nline two\n", encoding="utf-8")
    b.write_text("line one\nline two\n", encoding="utf-8")          # identical
    c.write_text("line one\nDIFFERENT\n", encoding="utf-8")          # changed
    assert s.in_sync({"hub": a, "core": b})
    assert not s.in_sync({"hub": a, "core": c})


# ── shared tier: fenced hub-only / downstream-only regions ──────────────────

def test_no_intermingled_shared_resources(report):
    bad = [f"{r['kind']}/{r['name']}" for r in report["intermingled"]]
    assert bad == [], (
        "A `shared` resource has a fence on the wrong side (HUB-ONLY in core, or DOWNSTREAM-ONLY "
        "in hub) — that intermingles hub- and downstream-specific code. Move it: " + str(bad)
    )


def _pair(tmp_path, hub_text, core_text):
    h = tmp_path / "hub.sh"; c = tmp_path / "core.sh"
    h.write_text(hub_text, encoding="utf-8"); c.write_text(core_text, encoding="utf-8")
    return {"hub": h, "core": c}


def test_shared_skeleton_ignores_fenced_regions(tmp_path):
    """Identical skeleton + DIFFERENT fenced regions → in sync; a skeleton change → not in sync."""
    hub = "shared line A\n# DUAL-SYNC:HUB-ONLY\nhub specific\n# DUAL-SYNC:END\nshared line B\n"
    core = "shared line A\n# DUAL-SYNC:DOWNSTREAM-ONLY\ndownstream specific\n# DUAL-SYNC:END\nshared line B\n"
    assert s.shared_in_sync(_pair(tmp_path, hub, core)), "fenced-only divergence must be allowed"

    core_drifted = core.replace("shared line B", "shared line CHANGED")
    assert not s.shared_in_sync(_pair(tmp_path, hub, core_drifted)), "a shared-skeleton change must be caught"


def test_intermingle_detection(tmp_path):
    """A HUB-ONLY fence in the core copy (or DOWNSTREAM-ONLY in hub) is flagged."""
    res = _pair(tmp_path, "x\n", "x\n# DUAL-SYNC:HUB-ONLY\noops\n# DUAL-SYNC:END\n")
    assert s.intermingle_problems(res), "a HUB-ONLY fence in the core copy must be detected"
    clean = _pair(tmp_path, "x\n# DUAL-SYNC:HUB-ONLY\nok\n# DUAL-SYNC:END\n", "x\n")
    assert not s.intermingle_problems(clean), "a correctly-sided fence must NOT be flagged"


def test_strip_specific_removes_both_fence_types():
    text = ("a\n# DUAL-SYNC:HUB-ONLY\nh\n# DUAL-SYNC:END\n"
            "b\n<!-- DUAL-SYNC:DOWNSTREAM-ONLY -->\nd\n<!-- DUAL-SYNC:END -->\nc\n")
    assert s.strip_specific(text).splitlines() == ["a", "b", "c"]
