# Sync Architecture

## 6 Sync Flows

### 1. Project → Hub (scan-projects)
```
Project repo (.claude/) → collate.py → dedup_check.py → PR to hub
```
- Triggered: Weekly cron or manual `gh workflow run scan-projects.yml`
- Script: `scripts/collate.py --all`
- Output: PR with new/updated patterns

### 2. Internet → Hub (scan-internet)
```
URLs/topics → scan_web.py → extract patterns → dedup_check.py → PR to hub
```
- Triggered: Weekly cron or manual `gh workflow run scan-internet.yml`
- Script: `scripts/scan_web.py --all`
- Output: PR with discovered patterns

### 3. Hub → Local Project (update-practices skill)
```
Hub registry → compare hashes → show diff → copy files → update sync-config
```
- Triggered: User runs `/update-practices` in Claude Code
- Script: `scripts/sync_to_local.py`
- Output: Updated `.claude/` files in local project

### 4. Hub → Registered Projects (sync-to-projects) — STAGE-1 RETIRED (2026-07-13)
```
[retired auto-trigger]  Hub push -x-> sync_to_projects.py
[current]               Hub edit → version bump → /plugin update in each project
[residual, manual-only] workflow_dispatch → sync_to_projects.py (rules + non-pack stack helpers)
```
- Plugin-covered content (workflows, sub-skills, agents, stack packs) is INSTALLED, not copied —
  all 5 enrolled repos migrated 2026-07-13 (#346 stage 2); propagation is CI-enforced by
  `check_plugin_version_bump.py`.
- The push-triggered auto-sync is OFF; `workflow_dispatch` remains for the residual
  copy-provisioned surface until stage 2 (owner-gated) decides its final form.
- Script: `scripts/sync_to_projects.py --all` (unchanged, manual)
- **Rules cannot ship as plugin content** (Claude Code has no plugin-rule mechanism), so a
  project's `.claude/rules/*.md` stays a one-time COPY forever — nothing above re-diffs it
  after provisioning day. `scripts/check_provisioned_rule_drift.py` (T-401) is the detector
  for that gap: it classifies every registered repo's rule copies against the hub's own git
  history (CURRENT / STALE / MODIFIED / PROJECT-ONLY) and flags a CONTRADICTION candidate
  when a project is stuck on content the hub later fixed — report-only, ticked weekly by
  `.claude/hooks/auto-pr-reconcile.sh`.

### 5. Local → Hub (contribute-practice skill)
```
Local pattern → validate → dedup check → PR to hub
```
- Triggered: User runs `/contribute-practice` in Claude Code
- Output: PR to hub repo

### 6. Enrolled Projects → Hub (telemetry aggregation)
```
Enrolled repos (.claude/ adoption + learnings.json) → aggregate_telemetry.py → effectiveness metrics in registry/patterns.json
```
- Triggered: Weekly cron (Friday) via `aggregate-telemetry.yml`, or manual
- Script: `scripts/aggregate_telemetry.py` (remote mode default; `--local` for a single repo)
- Output: Adoption signals + error-prevention effectiveness written back to `registry/patterns.json`. Unlike flows 1/2/5, this aggregates signals (not pattern files) and commits metrics directly — it does not open a pattern PR.

## Deduplication

3-level dedup prevents duplicates:

| Level | Method | When |
|-------|--------|------|
| 1 | SHA256 hash | Every scan |
| 2 | Structural (name+type+category+deps) | Every scan |
| 3 | Semantic (Claude Haiku API) | Internet sources only |

## Registry

`registry/patterns.json` tracks all patterns with:
- Hash, type, category, version
- Source provenance
- Dependencies
- Visibility (public/private)
- Tags and changelog
