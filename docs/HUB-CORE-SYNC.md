# Hub ↔ Core: scoping & dual-home sync

How to decide whether a resource (skill / agent / rule / hook) is hub-only or distributable,
and how the two copies of a resource that lives in BOTH places are kept honest. This is the
internal `.claude/` ↔ `core/.claude/` companion to `docs/SYNC-ARCHITECTURE.md` (which covers
hub ↔ projects / hub ↔ internet).

## 1. Where does a resource belong?

| Question | Home |
|---|---|
| Does it operate **the hub itself** (scan/synthesize/govern this repo)? | **hub-only** → `.claude/` |
| Is it generically useful to **any project**? | **distributable** → `core/.claude/` (+ registry) |
| Both — the hub *uses* it operationally AND it's generically useful? | **both** (dual-home) — a `.claude/` operational copy + a `core/.claude/` distributable copy |

**Default to distributable.** The hub's mission is to distribute proven patterns; keep something
hub-only only when it has no downstream meaning. `core/` patterns are **opt-in** (a project
provisions them via `recommend.py` / `/synthesize-project`), so distributing is never unsafe —
provisioning is the consent step. Build/dogfood in the hub first, then promote once proven
(genericize hub-specific deps — e.g. `scripts/dedup_check.py` → a pluggable `SECRET_SCAN_CMD`).

**Promotion goes both ways:** hub→core when a hub resource proves generically useful; core→hub
when the hub needs to *use* a distributable resource operationally (then it becomes dual-home).

## 2. Dual-home resources — the 3 tiers

A resource present in BOTH `.claude/` and `core/.claude/` MUST be classified in
`config/dual-home-resources.yml` as exactly one of:

- **`synced`** — the two copies MUST stay normalized-identical. A change to one side MUST be
  mirrored to the other. The gate fails on any drift.
- **`shared`** — mostly shared, with a few hub-specific and downstream-specific lines. The
  **shared skeleton** (everything outside the fences) MUST be identical; the fenced regions may
  differ. This is how a resource keeps its shared logic in lockstep while its specific bits
  legitimately diverge — *without intermingling* (see §3).
- **`divergent`** — substantially different variants; no sync enforced, just a documented reason.

## 3. `shared` fences — preventing intermingling

In a `shared` resource, hub-specific and downstream-specific lines are wrapped in markers (any
comment style — `#` for shell, `<!-- -->` for markdown):

```
# DUAL-SYNC:HUB-ONLY
<lines that exist only in the hub copy>
# DUAL-SYNC:END

# DUAL-SYNC:DOWNSTREAM-ONLY
<lines that exist only in the distributable copy>
# DUAL-SYNC:END
```

The gate enforces two invariants, so the two kinds of specific code **cannot intermingle**:
1. **Shared skeleton identical** — strip every fenced region from both copies; the remainder must
   match. A change to shared logic on one side fails the gate until mirrored.
2. **Correct-sided fences** — a `HUB-ONLY` fence may appear ONLY in the `.claude/` copy, a
   `DOWNSTREAM-ONLY` fence ONLY in `core/.claude/`. A misplaced fence is flagged `intermingled`.

## 4. The mechanism

- **`config/dual-home-resources.yml`** — the manifest (SSOT of every dual-home resource + its tier).
- **`scripts/sync_dual_home.py`** — `--check` (drift/intermingle report), `--list`,
  `--sync <name> --from hub|core` (copy one side to the other to reconcile a `synced` drift).
- **`scripts/tests/test_dual_home_sync.py`** — the CI gate: every dual-home resource must be
  classified; `synced` must be identical; `shared` skeletons must match with correctly-sided
  fences; no stale manifest entries; no double-classification.

A NEW dual-home resource (or a drifted `synced` one) fails CI until it's classified / reconciled —
so drift can never land silently.

## 5. When you change a dual-home resource

- **`synced`** → make the change on one side, then `python scripts/sync_dual_home.py --sync <name> --from hub|core`.
- **`shared`** → change the shared skeleton on BOTH sides (keep them identical); change a fenced
  region on only its own side.
- **`divergent`** → change each side independently; reconcile by hand only the parts relevant to both.

> **Conversion candidates:** `auto-git.sh` and `auto-pr.sh` are currently `divergent` but are
> genuinely mostly-shared (the divergence is the secret-scan block + commit trailer). They can be
> converted to `shared` once their incidental comment drift is reconciled and the genuine specific
> regions fenced. `git-branch-lifecycle` is the worked `shared` example.
