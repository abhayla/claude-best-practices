# Sync Architecture

## 5 Sync Flows

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

### 4. Hub → Registered Projects (sync-to-projects)
```
Hub push → sync_to_projects.py → create PR per project
```
- Triggered: Push to main (core/, stacks/, registry/)
- Script: `scripts/sync_to_projects.py --all`
- Output: PRs to registered project repos

### 5. Local → Hub (contribute-practice skill)
```
Local pattern → validate → dedup check → PR to hub
```
- Triggered: User runs `/contribute-practice` in Claude Code
- Output: PR to hub repo

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
