# Vendor-estate execution routing — design (owner-ratified forks, 2026-08-07)

> **What this is.** The execution-side extension of the artifact filing rule (gorefer
> CLAUDE.md §6b + the 2026-08-06 moves): not just *where vendor files live*, but *where
> vendor work runs*. Brainstormed and fork-decided with the owner 2026-08-07 (rule
> strength: routing-default-with-recorded-escape; Zoho lane: register the subfolder).

## The problem (both failure modes observed live)

- **No artifact rule bite:** the Deluge-functions skill sat in gorefer for weeks though it
  is org-wide Zoho know-how (fixed 2026-08-06 by moving it to Zoho-Project).
- **No execution rule at all:** P0-A (pure Zoho-estate work: console function + workflow
  rule) ran from a gorefer session with zero recorded justification. It happened to be the
  right call (the verification loop needed gorefer prod logs in the same minute) — but
  "happened to be right" is luck, not policy.

## The rule (three enforcement points — Approach A, owner-approved)

### 1. Global rule (all sessions) — body in the HUB, pointer in each machine's `~/.claude/CLAUDE.md`

**v1.1 amendment (owner, 2026-08-07): the rule must also govern the Windows VPS.** The VPS
runs the same projects (synced from GitHub) — but `~/.claude/CLAUDE.md` is a per-machine file
that git cannot sync. So the rule body does NOT live there. It lives in the hub:
`core/.claude/rules/vendor-estate-routing.md` — the same pattern as `decision-authority.md`
and `model-cost-routing.md`, which the global file already only points at. Each machine's
`~/.claude/CLAUDE.md` gets a 3-line always-on reinforcement + pointer (one-time edit per
machine, rarely changes). The hub repo git-syncs to the VPS, so the body arrives with a
normal pull — no second copy to drift.

**Path roots differ per machine** — the rule file states both, like the get-work-done
pointer already does: PC root `D:\Abhay\VibeCoding\`, Windows VPS root `C:\Abhay\`
(so Zoho lane = `D:\Abhay\VibeCoding\5Wealths\Zoho-Project` on the PC,
`C:\Abhay\5Wealths\Zoho-Project` on the VPS; Wati lane likewise).

The rule text (goes in the hub rules file):

> **Vendor-estate routing (owner rule, 2026-08-07).** Work that changes a vendor estate
> runs in that vendor's project lane:
> - **Zoho estate** (CRM functions/Deluge, workflow rules, fields/modules, org config,
>   WA_Send_Queue pipeline) → `D:\Abhay\VibeCoding\5Wealths\Zoho-Project` (session or
>   dispatched worker).
> - **Wati estate** (templates, chatbot flows, broadcasts, keyword routing, tenant
>   config) → `D:\Abhay\VibeCoding\Wati-Project`.
>
> **The boundary test — "what does the task CHANGE?"**
> - Changes the vendor estate → vendor lane.
> - Changes an app repo or its prod (gorefer etc.) → that app's lane, even when it calls
>   vendor APIs; adapters + CI-coupled contract docs stay with the app (gorefer §6b).
> - Changes BOTH (P0-A shape) → **recorded escape**: may run in the app session IF
>   (a) the vendor project's skills are loaded FIRST, and (b) the vendor project's
>   registry/docs are updated in the same turn. An unrecorded cross-estate run is a
>   defect even when the outcome is right.
>
> Sessions cannot be conjured: only the owner opens interactive sessions. When work
> belongs in a vendor lane and needs interactivity, say so and stop; otherwise dispatch a
> background worker into the vendor project's registry path.

### 2. Dispatcher intake (background workers) — goes in the get-work-done skill (STEP 1)

> **Estate classification (owner rule, 2026-08-07):** at intake, classify each task by
> what it CHANGES (vendor estate vs app repo/prod vs both — boundary test in the global
> vendor-estate routing rule). Vendor-estate tasks dispatch into that vendor project's
> registry path so its CLAUDE.md + skills load. Both-estates tasks name the primary
> verification loop's repo as the lane and record the escape in the contract's
> status_log.

### 3. The lanes themselves

- **Wati-Project**: already a registered dispatch repo with CLAUDE.md + skills. No change.
- **Zoho-Project** (the gap): add a `GWD settings.json → repo_registry` entry:
  - key `zoho-project`; `path: D:\Abhay\VibeCoding\5Wealths\Zoho-Project`;
    `remote: https://github.com/abhayla/5wealths.git` (subfolder of the 5wealths repo);
    `vps_path: C:\Abhay\5Wealths\Zoho-Project`;
  - `_note`: commits land in the 5wealths repo (direct-commit convention, pull-rebase
    first); workers MUST stay inside the `Zoho-Project/` subtree; `.claude/` is
    gitignored in 5wealths — skill files are force-added deliberately (precedent
    2026-08-06 `1eccd08`). **Registry preflight caveat:** `preflight-guard.ps1` asserts
    remote — 5wealths remote is shared with the whole workspace; the note must warn
    workers to never touch files outside the subfolder.
  - Write `Zoho-Project\CLAUDE.md`: entry-point map (deluge/ SSOT, `.claude/skills/`
    incl. the relocated `gorefer-zoho-deluge-functions` + `manage-zoho-functions`, the
    WA_Send_Queue wiring, zapikeys in GLOBAL.env, UI-paste-only authoring rule, the
    CRM-Plus tab-recycle + stale-list-cache traps, the v8-API-first rule + missing
    settings scope).

## Fleet propagation — what syncs itself vs what needs hands (v1.1)

| Artifact | Reaches the VPS how |
|---|---|
| Rule body (`core/.claude/rules/vendor-estate-routing.md`) | hub repo `git pull` — automatic |
| get-work-done intake step (hub SKILL.md) | hub repo `git pull` — automatic |
| GWD registry entry (`settings.json`) | GetWorkDone repo `git pull` — automatic |
| `Zoho-Project\CLAUDE.md` | 5wealths repo `git pull` — automatic (root-level file, NOT under the gitignored `.claude/`) |
| `~/.claude/CLAUDE.md` 3-line pointer | **manual, once per machine** — PC in this session; VPS in the next VPS session (or a TODO-Manual card if no session is planned) |

Honest limit: the per-machine pointer is the one thing that can drift — a fresh machine or a
reinstalled profile silently loses the rule until the pointer is re-added. Mitigation: keep the
pointer to 3 lines so re-adding is trivial, and the hub rule file is the SSOT either way (a
session that reads the hub rules dir still finds it).

## What this rule would have changed, concretely

- The deluge skill would have been authored in Zoho-Project on day one.
- P0-A still runs from the gorefer session (both-estates escape) — but with the vendor
  skills loaded from the start (the timestamp trap was documented in Zoho-Project files
  I read late) and the registry updated in the same turn instead of at day's end.
- A future "fix the Wati chatbot menu" task dispatches into Wati-Project automatically
  instead of riding whichever session noticed it.

## Non-goals (YAGNI)

- No hard blocking, no hooks, no new tooling — three text surfaces + one registry entry.
- No Zoho-Project repo carve-out now; "graduates to its own repo if the lane earns it."
- No change to gorefer's §6b (adapters/contract docs stay put — CI-coupled).

## Implementation checklist (≈1–2 h)

1. Write the rule body to hub `core/.claude/rules/vendor-estate-routing.md` (§1, with both
   machine path roots); commit + push hub main → VPS gets it on next pull.
2. `~/.claude/CLAUDE.md` (this PC): add the 3-line reinforcement + pointer.
3. Hub `get-work-done` SKILL.md STEP 1: add the estate-classification paragraph (§2);
   the thin pointer copies in projects need no change.
4. `GWD\settings.json`: add the `zoho-project` registry entry (§3) — syncs to the VPS via
   the GetWorkDone repo.
5. Write `Zoho-Project\CLAUDE.md`; commit to 5wealths — syncs to the VPS via git.
6. VPS `~/.claude/CLAUDE.md`: add the same 3-line pointer — next VPS session, or a
   TODO-Manual card if none is planned.
7. Record the rule's existence in gorefer `COORDINATION.md` (one STATUS line) so the
   Engineer/DA channel knows routing changed.

## Risks / honest limits

- The escape hatch depends on sessions actually recording it — same honor-system class
  as `[skip-contract-doc]`; it is deliberately covered by the monthly keeper gate-audit
  habit only if we add the grep (follow-up: extend `gate-audit.ps1` to grep vendor-lane
  escapes once a marker phrase exists; not in v1).
- 5wealths-subfolder workers share a repo with unrelated personal content; the registry
  note constrains them by instruction, not mechanism. If a worker ever strays outside
  the subtree, that is the trigger to do the repo carve-out.
- The boundary test is judgment at the margins (e.g. editing a Zoho webhook's GoRefer-side
  HMAC secret touches both); the escape hatch exists precisely for those.
