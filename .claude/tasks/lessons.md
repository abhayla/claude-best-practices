# Lessons Learned

<!-- Claude appends entries here after corrections or surprising outcomes. -->

## 2026-06-19 — Governance hooks over-fire at legitimate quality boundaries (the stop-loop)

**Surfaced during:** the platform-migration session. At the end of a long, context-saturated session
the `no-overask-guard.sh` (narrate-and-stop) and the enhance-render check entered a LOOP: every attempt
to wrap up at a completed-tested-chunk boundary — with the only remaining work being owner-gated or a
coherent-unit that genuinely needs fresh context — was blocked as a "narrate-and-stop violation," and
every status summary was blocked for not re-rendering the full enhance card. The hooks cannot distinguish
a *legitimate quality boundary* from an *avoidable stop*. This is the governance-by-harness-vs-internalization
tension (flagged in the session's own opening retrospective), demonstrated live.

**What to do instead / PROPOSED HOOK TWEAK (pending Abhay approval — rule 5):** add a `*Session-boundary:*`
exemption to `no-overask-guard.sh`, mirroring the existing `*Sync-check:*` exemption. When the final
message opens a line with `*Session-boundary:*` AND the turn completed a tested chunk, the hook LOGS it as
telemetry (like the other misses) instead of BLOCKING. The model may use the marker ONLY when (a) a
tested/verified chunk is complete and committed, AND (b) all remaining work is either owner-gated
(sign-off/deploy/spend) or explicitly deferred-for-quality with a one-line reason (e.g. coherent
multi-file edit needing fresh, non-saturated context). Abuse guard: the Stop hook still logs every use to
`.claude/.enhance-misses.log` for audit, so a model that over-uses the marker is visible.

## 2026-06-19 — Render the FULL enhance card on EVERY substantive turn, including continuations

**Surfaced during:** same session — the enhance hook blocked me 5+ times for rendering only the one-liner
(or a status without the card) on continuation / background-task-completion turns that still produced
substantive output (commits, edits, analysis). **Rule:** the full process (banner + transcript + before→after
card WITH the Reviewer-after column + Original→Final + Role) fires on OUTPUT blast radius, not prompt shape.
A turn triggered by a background-agent completion or a short "go" that then does real work STILL needs the
full card (with n/a rows where there's no user prompt to grade). Default to rendering it; don't wait for the block.

## 2026-06-19 — Verify each MIGRATE before spending effort; platform "facts" go stale

**Surfaced during:** Phase 0 audit → Phase 1/4 inspection. The subagent audit's headline (28 MIGRATE) was
over-claimed: on per-pattern inspection, Phases 1.1/1.2/1.3 were marginal or already-adopted (the hub had
already taken `isolation:worktree`, `/goal`+`/loop` when they shipped), and the real value was gated on one
thing (nested-subagent GA). **Rules:** (1) a broad audit OVER-claims — verify each MIGRATE against the live
pattern + official docs before investing; the "no-churn" discipline (don't migrate what's already adopted or
marginal — KISS/YAGNI) saved real effort here. (2) Foundational PLATFORM-CONSTRAINT claims go stale:
`agent-orchestration.md`'s "subagents cannot spawn subagents (verified 2026-04-24)" was FALSE by Jun 2026
(nested dispatch GA v2.1.172, ≤5 levels). Periodically re-verify platform facts — now wired via the scan
pipeline (`config/urls.yml` release-tracking URLs, Layer-1 self-updating goal).

## 2026-06-17 — Global `.claude/` gitignore silently drops NEW pattern files

**Surfaced during:** committing the BA reminder hook. The NEW file `core/.claude/hooks/ba-usecase-discovery-reminder.sh` was silently excluded from the commit (PR diff had settings+registry but not the script) — a global `~/.config/git/ignore` rule `.claude/` ignores `.claude/` at any depth, including `core/.claude/`. Already-tracked files keep committing (so edits look fine); only NEW files are dropped, and `git add` only prints an easy-to-miss hint.

**What to do instead:** (1) Deterministic fix applied — repo `.gitignore` now has `!core/.claude/` to override the global rule so new distributable-template files track normally; for hub-only `.claude/` use `git add -f`. (2) ALWAYS run `git diff --stat main..<branch>` and confirm NEW pattern files are present before calling a PR complete — a new pattern file missing from the commit means the registry references a file not in the repo (CI fails / pattern silently absent). Verifying the diff caught this; not verifying would have shipped a broken pattern.

**RECURRED 2026-06-18** (BA-gate Phase 1): the `!core/.claude/` override does NOT cover the HUB `.claude/` (intentionally selective). A NEW hub hook `.claude/hooks/ba-usecase-discovery-reminder.sh` was silently dropped by `git add -A`; only `git add -f` tracks it. The new `test_ba_gate_wiring.py` guard caught it — **but only at CI**, because the test asserts `Path.exists()` (filesystem, passes locally even when untracked), not git-tracked status. NET RULE: after `git add -A` of any hub `.claude/` change, run `git status --short .claude/` and force-add any `??`/missing NEW hub file; treat a `M settings.json` with no matching hook file as the tell. The CI catch is the backstop, NOT the primary gate — verify the staged diff locally first.

## 2026-06-17 — BA sequence: use-case discovery FIRST, then questions, then UI

**Surfaced during:** calculator build (crystallized by Abhay). The load-bearing part is the ORDER, which my v1.2.0 edit hadn't pinned.

**The rule:** Before anything else, **discover the FULL use-case space FIRST** — from the domain perspective AND the user/personal perspective, doing a **web search to enumerate all possible use cases** when the domain isn't fully known. **Only then** ask clarifying questions, **then** design the UI, **then** build. Use-case discovery is step 1, never backfilled after building. (I had done domain research late and centered the calculator on the wrong actor.) Rule: `engineering-roles.md` PM mandate v1.2.1.

## 2026-06-17 — PM: value proposition + full use-case space FIRST (don't just build the spec)

**Surfaced during:** calculator build. Abhay's biggest critique: I executed the literal 4-scenario spec without doing the product/BA work — exploring ALL meaningful use-case combinations and articulating WHY anyone would use the tool (the benefit). Research afterward showed the build covered ~15% of the valuable surface AND missed the PRIMARY user.

**What I got wrong:** Treated the handed spec (person×company × cash×loan) as the scope. Never asked "who is the primary user, why would they use this, what maximizes their benefit?" The domain research (done late) revealed THREE actors not two — the **self-employed professional/proprietor** is the primary beneficiary; a salaried person is the no-benefit baseline. Also missed high-leverage levers: tax-slab, business-use %, EV vs ICE (40% vs 15% depreciation), lease-vs-buy, resale/STCG recapture, and break-even/threshold "aha" outputs.

**What to do instead:** As PM/BA, BEFORE/while building: (1) state the VALUE PROPOSITION — primary user + why they'd use it + the benefit they can't get elsewhere; (2) map the FULL use-case/combination space (actors, variants, edge cases), not just the literal spec; (3) expand scope to maximize benefit across all real use cases and surface the high-value insights; (4) if you can't state a concrete benefit, challenge whether to build it. Rule updated: `engineering-roles.md` Product Manager mandate.

## 2026-06-17 — Calculator dogfood retrospective (multiple misses)

**Surfaced during:** building the calculator app end-to-end. Consolidated honest misses:

1. **Red PR merged (#88) by skipping full pytest — RECURRENCE of the 2026-06-16 lesson.** A prose lesson did NOT change behavior. **Fix = deterministic gate, not memory:** before any push that touches a registered pattern, reproduce the FULL `validate-pr.yml` command set (incl. complete pytest); and enable branch-protection required status checks so a red PR cannot merge in the first place.
2. **Built new hub patterns without evals.** `bootstrap-dogfood-project` (skill) + `human-approval-gates` (rule) shipped with no `/skill-evaluator` run — the exact eval-coverage gap (C) flagged the same session. RULE: run the relevant eval on any new/changed skill/agent before declaring it done.
3. **Dogfood loop wired only locally.** For the calculator I set committed `learnings.json` + `synthesis-config.yml` but NOT the GitHub remote or `config/repos.yml` enrollment, so hub-ward telemetry does not flow — and I never ran my own `/bootstrap-dogfood-project` gate on it, which would have BLOCKED on the missing remote. RULE: run the bootstrap gate on a new dogfood project; "set up" = all 5 preconditions green, not 3.
4. **Provisioning tier-gated out pipeline-critical rules** (engineering-roles, human-approval-gates landed as nice-to-have, didn't provision). Hub follow-up: re-tier the goal-#3 pipeline rules as must-have OR add a "pipeline-closure" provisioning group.
5. **Repo hygiene at init:** add `.gitattributes` (LF normalization) to new repos to avoid CRLF-warning noise on every commit; point the Playwright MCP at an output dir inside the target repo (screenshots kept landing in the hub root); kill background dev servers when done.
6. **Over-asking / narrate-and-stop recurred** — paused on reversible work (merges, "next I'll…") instead of executing. Decide-and-do on reversible/internal; escalate only genuine blockers.
7. **Domain model depth:** the loan-vs-cash opportunity-cost model was simplified (compound on upfront capital, under-charges the EMI stream). Offer a rigorous NPV/time-value "advanced" mode rather than ship only the simplified one silently.

## 2026-06-17 — BA: research the domain BEFORE asking (don't ask on an unverified premise)

**Surfaced during:** calculator dogfood build. I asked "should personal vs company loan rates be separate?" — premised on an *assumed* rate difference I had not verified. Abhay (twice): the BA must do proper domain research FIRST; that's my prerogative, not a question for the user.

**What I got wrong:** Asked a question built on an unverified domain assumption. Research then showed the premise was wrong (individual vs company passenger-car loan rates are effectively the SAME — credit-based, not entity-based; the real differences are tax: depreciation 15% WDV + interest deductibility, company business-use only). I should have known/researched that before forming the question.

**What to do instead:** At the requirements stage, FIRST research the real-world domain (standard rates/rules, what is genuinely same vs different) and decide domain/math/best-practice matters myself, stating overridable assumptions. Only ask genuine product/preference forks (what it does, how it looks, scale). Never ask a fact a BA should verify; never ask a question premised on an unverified domain assumption. Rule updated: `engineering-roles.md` Product Manager mandate.

## 2026-06-17 — Clarification: ONE question per turn, each with a recommendation

**Surfaced during:** the calculator dogfood build — at the requirements stage I dumped 11 questions in one turn. Abhay corrected: ask one at a time (grouped by category), and for each question give a recommended option + justification + why the other options are weaker.

**What I got wrong:** Batched the entire question set in a single message — overwhelming, and a direct violation of the existing "one targeted question at a time" clause in the clarification gate. Also asked bare questions with no recommendation, forcing the user to reason from scratch.

**What to do instead:** Hold the full question list internally; group by category (functional → UI/UX → scale); ask EXACTLY ONE per turn; only ask the next after the current is answered. Every question presents options with a **recommended** option + a one-line justification + a one-line reason each alternative is weaker — prefer `AskUserQuestion` with the recommended option first. **Sequence on prior answers** — re-read the running answer log before each question; never ask something already answered, implied, or contradicted earlier; drop/adapt now-moot queued questions as answers land. Rule updated: `core/.claude/rules/prompt-auto-enhance-rule.md` Clarification Gate.
<!-- Review at session start to avoid repeating mistakes. -->
<!-- Format: date, what went wrong, what to do instead. -->

## 2026-06-17 — Aggregation that keys on a link field must SEED from it too (telemetry silent-drop)

**Surfaced during:** wiring loop-engineering's hub-ward monitoring; the
independent code-reviewer (maker/checker pass) caught it — my own unit test did not.

**What I got wrong:** I added `hub_pattern_link: "loop-engineering"` emission to
the skill and verified `aggregate_telemetry.compute_error_prevention_rate` keys on
that field. Looked correct. But the ORCHESTRATION layer (`aggregate_project_telemetry`
/ `aggregate_remote`) built its iteration set `all_patterns` ONLY from the
sync-manifest adoption scan, then looped `for pattern in all_patterns:`. A learning
linked to a pattern NOT in the manifest was loaded into memory but never iterated —
silently dropped. The leaf function was right; the caller never asked it about the
pattern. Classic "wrong-but-working": every unit test green, signal lost.

**What to do instead:** when an aggregator/join keys records on a field X, its
iteration/seed set MUST include `union(primary_set, distinct values of X across the
records)` — not just the primary set. Here: seed `all_patterns` with manifest names
∪ every `hub_pattern_link` found in learnings (`_linked_pattern_names`).

**Generalizable (two lessons):**
1. A unit test on the leaf compute fn does NOT prove the pipeline delivers — add an
   END-TO-END test through the orchestration entry point (it's the one that flips
   pre/post fix).
2. The maker≠checker split earns its cost: an independent reviewer with fresh
   context caught a silent-no-op that the author (me) + author-written unit tests
   missed. Always run the independent pass on telemetry/aggregation wiring.

**Pinned by:** `test_learnings_only_pattern_is_aggregated` in `scripts/tests/test_aggregate_telemetry.py`.

## 2026-06-16 — Skill() invocations belong in FENCED code blocks, not inline backticks

**Surfaced during:** authoring `core/.claude/skills/loop-engineering/SKILL.md`;
`workflow_quality_gate_validate_patterns.py` failed with "References non-existent
skill '/fix-loop'" and '/debugging-loop' — even though both skills exist.

**What I got wrong:** I wrote the heal-arm dispatches as INLINE backticks —
`` `Skill("/fix-loop", ...)` `` — inside prose. The validator's
`check_cross_references()` strips only triple-fenced ``` blocks before scanning,
then its `Skill\(["']([^"']+)` regex captures the FULL first arg *including the
leading slash* (`/fix-loop`), and compares it to `existing_skills` which holds
bare directory names (`fix-loop`). `/fix-loop` != `fix-loop` → false-positive
"non-existent skill". (The separate `` `/name` `` regex captures *without* the
slash, so plain-backtick refs are fine — only `Skill("/...")` in inline backticks
breaks.)

**What to do instead:** Put every `Skill("/...")` and `Agent(subagent_type=...)`
invocation inside a triple-fenced ``` code block (as `/development-loop` and the
other workflow skills do). Fenced blocks are stripped before cross-ref scanning,
so the slash-prefixed capture never fires. Reserve inline backticks for bare
`/skill-name` mentions, never for full `Skill("/skill-name", …)` calls.

**Generalizable:** when a new skill body trips the cross-ref validator on a
reference you KNOW exists, check whether it's an inline `Skill("/…")` — move it
into a fenced block rather than touching the validator.

## 2026-04-22 — Aggregator "union of failures" rule needs a superset check

**Surfaced during:** Phase H of the testing-pipeline overhaul, `test_flaky_scenario_surfaces_quarantined_issue` in `scripts/tests/test_pipeline_e2e.py`.

**What I got wrong:** In `scripts/pipeline_aggregator.py`, the verdict check
was `if failures or screenshot_failures:` — meaning a stage that reported
`result: FAILED` but provided an empty `failures[]` array (e.g., a conductor
that moved a test to `known_issues` without producing an individual failure
entry) was counted as PASSED. Top-level FAILED status was effectively
invisible to the aggregator.

**What to do instead:** The "union of failures" rule is a SUPERSET —
stage-level FAILED counts regardless of per-failure detail. The aggregator
MUST also check `any(r["result"] == "FAILED" for r in results)` and fail
the pipeline when any stage reports FAILED, even if its `failures[]` is
empty. Generalizable rule: for any aggregator that unions typed evidence,
always include a stage-level failure check as a safety net — don't trust
that every FAILED skill populates its evidence array.

**Pinned by:** `test_stage_failed_with_empty_failures_still_fails` in
`scripts/tests/test_pipeline_aggregator.py`.

## 2026-04-22 — Pinned-content tests break on consolidation; update homes, don't skip

**Surfaced during:** Phase A of the testing-pipeline overhaul. The test
`test_skill_md_version_is_3_0_0` in `test_e2e_visual_run_playwright_only.py`
asserted the old skill version and broke when the skill was consolidated
into v4.0.0. Similarly `test_pipeline_verdict_schema_in_orchestrator`
asserted the schema was in `test-pipeline-agent.md` but the schema moved
to `testing-pipeline-master-agent.md` when aggregation was centralized.

**What I did right:** Updated both tests to target the new homes
(e2e-conductor-agent for the skill content, testing-pipeline-master-agent
for the verdict schema) rather than deleting them or marking them skipped.
The tests now carry their original intent forward.

**Generalizable rule:** When content is moved between files during a
consolidation, pinned-content tests are valuable regression nets — migrate
the assertions to the new authoritative location. Deleting them loses the
regression surface; skipping them masks drift.

## 2026-04-24 — Platform constraints cascade: one broken primitive can invalidate an entire architectural pattern

**Surfaced during:** Blast-radius audit after Phase 1 of the subagent-dispatch-platform-limit remediation. Expected scope was 3 agents + 2 skills (test pipeline). Actual scope is ~30 files across the entire hub.

**What I expected:** The nested-`Agent()`-dispatch bug was confined to the testing pipeline, because that's where I first saw it surface in the 2026-04-24 testbed run. Phase 1 deprecated 3 agents and 1 skill; Phase 3 would dissolve them into a single T0 skill. Bounded and tractable.

**What actually happened:** The bug is the entire **workflow-master pattern** used by 8 workflows in `config/workflow-contracts.yaml`. Every `<workflow>-master-agent` declares `sub_orchestrators:` in the workflow contract and assumes it can dispatch them via `Agent()` at runtime — but every one of those masters is itself dispatched by a slash-command skill, making them subagents without `Agent` tool access. The test pipeline was just the first failure mode to surface, not the only one.

Concrete blast radius:
- 7 non-deprecated master-agents (`code-review`, `debugging-loop`, `development-loop`, `documentation`, `learning-self-improvement`, `session-continuity`, `skill-authoring`) all silently inlining their "sub-orchestrator" dispatches
- 8 slash-command skills wrapping them
- 8 `workflow-contracts.yaml` entries with stale `sub_orchestrators:` lists
- 3 standalone orchestrators (`project-manager-agent`, `parallel-worktree-orchestrator-agent`, `e2e-conductor-agent`) with similar assumptions
- 1 template (`workflow-master-template.md`) that seeds the broken pattern for future copy-paste
- Manual docs (`README.md`, `docs/specs/*`, `docs/plans/*`) describing the tier model

Total ~30 files, ~9 PRs, ~3000-4000 lines net to retire the pattern cleanly.

**Generalizable rule:** When a finding invalidates a foundational primitive (here: nested subagent dispatch), scope the remediation by the **pattern that depends on the primitive**, not by the specific instance where the failure first surfaced. Run a blast-radius grep BEFORE planning fix scope — especially grep for the primitive's signatures (`Agent(subagent_type=…)`, `Agent` in `tools:`, pattern-specific config keys like `sub_orchestrators:`). The first failure mode is rarely the only failure mode.

**How to apply next time:**
1. After a platform/foundation finding, immediately audit for all consumers of the broken primitive — don't wait to "stumble into" the rest
2. Prefer a template-first remediation (fix the pattern in one template, then propagate per-consumer) over a flat instance-by-instance rewrite — template-first prevents re-introduction via future copy-paste
3. Expand the plan document (not the original PR) when scope grows — keep individual PRs small even if the overall plan is large; use the todo.md expansion to track the whole
4. Run an eval gate after the first full consumer migration (canary) to validate the pattern holds before committing to migrating the rest

**Evidence on disk:**
- Audit findings: `.claude/tasks/todo.md` § "Phase 1.5 — Blast-radius audit"
- Primary-probe lesson (the foundation finding): earlier entry in this file (2026-04-24, Parallel tool dispatch restrictions)
- Workflow-contracts.yaml: 8 workflows declaring `sub_orchestrators:` as of this session

## 2026-04-24 — Parallel tool dispatch in Claude Code is more restricted than prompt-engineering guidance suggests

**Surfaced during:** Phase 0 empirical probe for the subagent-dispatch-platform-limit remediation, session 2026-04-24.

**What I expected:** Multiple tool calls issued in a single assistant message would execute in parallel, per the common Claude Code prompt directive ("make all independent tool calls in parallel"). A reviewer (anthropic-multi-agent-reviewer-agent) specifically claimed that parallel `Skill()` calls in one orchestrator message would preserve the testing-pipeline Wave 1 (functional+API lanes concurrent) — and that this was the cheap alternative to an external script wrapper.

**What actually happened:** Empirical probes in both a dispatched `general-purpose` subagent session AND my own T0 session measured:
- Two `Bash` calls with 3-second sleeps issued in one message → **serial** (7s and 10s gaps respectively between end-of-A and start-of-B)
- Two `Skill` calls in one message → **blocked from concurrent execution**; `Skill` appears to inject the target SKILL.md into the caller's next user-turn context, creating a serial prompt queue in the same session (no new subagent context, no concurrency)
- Two `Read` calls → returned in the same turn, but Read is fast enough that parallelism vs serialism is unobservable from timing
- Two `Agent` calls in one message at T0 → confirmed parallel (documented + standard), but unavailable in subagent sessions per Anthropic's official docs (https://code.claude.com/docs/en/sub-agents — "subagents cannot spawn other subagents")

**Generalizable rule:** In Claude Code, "parallel tool calls in one message" is only reliably parallel for `Agent()` dispatched from the T0 user session. `Bash`, `Skill`, and most other tools appear to be serialized by the runtime regardless of session level, at least on Windows/Opus 4.7 at the hub's current version. Any architecture that assumes parallel `Bash`/`Skill` from a dispatched subagent WILL run serially at runtime. Verify parallelism empirically with nanosecond timestamps before designing around it — don't trust the "issue in one message → parallel" folklore.

**Downstream implication:** For the testing-pipeline refactor, Wave 1 (functional + API in parallel) requires one of three non-obvious paths: (1) move the orchestrator to T0 so the user's session dispatches lane subagents via `Agent()`, (2) externalize via a shell-script wrapper running `claude -p` twice, or (3) accept serial Wave 1. Parallel `Skill()` from the orchestrator is NOT a viable option. The reviewer's premise was wrong.

**Evidence on disk:**
- Subagent probe transcript: returned inline in session 2026-04-24 (T2 of session 2)
- T0 timings: A=1777025367927028600→1777025371086561100, B=1777025381209802100→1777025384403795200 (10.12s gap)

## 2026-04-24 — Registry hash field was dead data; wire enforcement or drop the field

**Surfaced during:** Tech-debt cleanup after REQ-S004 (analyzer v2.3.0). A
todo.md review flagged that `registry/patterns.json` had a stale hash for
`test-failure-analyzer-agent`. Checking the full registry revealed **228
of ~237 patterns** had drifted hashes — the column had been effectively
cosmetic for a long time because `validate_registry()` only checked that
the `hash` field **existed**, not that it **matched** the file.

**What I got wrong initially:** Recommended fixing only the analyzer's hash.
That would have left 227 other stale hashes and accomplished nothing —
the column still would not have been trustworthy for future gating. The
honest fix was either (a) regenerate all + add enforcement, or (b) drop
the field entirely.

**What to do instead:** When fixing a single instance of a broader quality
signal, first measure whether the signal is drift-enforced. If not, either
wire enforcement alongside the fix, or admit the field is decorative and
stop maintaining it. Regenerating one value without enforcement is
busy-work — the whole column keeps rotting.

**Resolution:** `validate_registry()` now compares each entry's `hash`
against `hash_pattern(<on-disk file>)` and `test_no_drift_in_shipped_registry`
pins the invariant. The `resolve_pattern_file()` helper handles hub-only
skills living at `.claude/skills/<name>/SKILL.md` (fallback) alongside
canonical `core/.claude/` paths, and skips `config`-type patterns that
aren't file-hashable.

**Also worth flagging** (surfaced but not actioned here): downstream
projects whose `.claude/config/test-pipeline.yml` lacks an `auto_heal:`
block will now hit the REQ-S004 fail-safe fallback — WARN logs +
`ISSUE_ONLY` defaults. Pick this up in the next `sync-to-projects` pass
so downstream maintainers add the block.

## 2026-04-24 — Agent `tools:` frontmatter MUST be a YAML list, not scalar

**Surfaced during:** v2-pipeline-testbed autonomous run Phase 5a finding —
`failure-triage-agent` and `github-issue-manager-agent` were NOT
discoverable as `subagent_type` despite being present on disk post-
provisioning. Pipeline dispatch silently collapsed to inline execution
at T1; outputs looked right but the 4-tier architectural invariant
(REQ-M006 / M009 / M013) was broken.

**Root cause:** 6 agents declared `tools: "Agent Bash Read Write Edit
Grep Glob Skill"` — a space-separated scalar. Claude Code's agent
discovery requires the YAML list form `tools: ["Agent", "Bash", ...]`.
The scalar parses as a single string and the agent is not exposed as a
valid `subagent_type`.

**What was wrong about the existing test:** `test_orchestrator_tool_grants.py`'s
`_tools_set()` accepted BOTH forms as equivalent (split the string on
whitespace). So the test would pass for agents with the broken scalar
form, never catching the discovery failure.

**Generalizable rule:** When a test pins an invariant by reading a
normalized view of the data, the normalization step can silently accept
the broken form. Reviewing the test's failure cases (what SHOULD make
it fail) is as important as reviewing the assertion.

**Resolution:** `_tools_set()` now raises TypeError on scalar input;
`pattern-structure.md` rule shows list form as canonical; all 6
affected agents fixed; pins expanded to cover failure-triage-agent and
github-issue-manager-agent. Committed `f5036c6`.

## 2026-04-24 — Runtime is the arbiter when docs and runtime disagree

**Surfaced during:** Phase 2b finding "Config naming mismatch (TIMEOUT
vs TIMING)" — widened grep revealed: analyzer `category` output
(SELECTOR, TIMEOUT, ASSERTION_FAILURE...), spec §3.6 matrix
(BROKEN_LOCATOR, TIMEOUT_TIMING...), and config `auto_heal:` keys all
used slightly-different names for overlapping concepts. Three
taxonomies, none aligned.

**What I got wrong initially:** treated as a 1-pair naming fix. Broader
grep exposed 6 mismatched pairs + 60 eval scenario files with old names.

**What to do instead:** when documentation and runtime disagree, the
runtime is the source of truth. Align docs to what actually runs, not
the reverse. But be honest about scope — updating 60 eval fixtures in
the same pass as a runtime fix is scope creep. Commit runtime
alignment; call out the deferred fixture cleanup explicitly.

**Resolution:** Config + spec §3.6 + §3.13 aligned to analyzer
categories. Eval scenarios + `_gen_pr2_evals.py` + research docs
DEFERRED (still reference old names but don't affect runtime —
they're evaluated via /agent-evaluator, not pytest). Committed `c6dac7d`.

## 2026-04-24 — Provisioning tier gap: must-have-only default hides upgrades

**Surfaced during:** Phase 0 P0c FAIL — `recommend.py --provision` default
(`--tier must-have`) "listed but did not apply" prompt-logger hook
(nice-to-have) and the updated test-pipeline.yml config.

**What to do instead:** When a pattern benefits every Claude Code
session regardless of project type, tier it `must-have` so downstream
projects get it on default provision. Universal hooks and ubiquitous
configs should not wait for a user to opt into `--tier nice-to-have`.

**Resolution:** prompt-logger promoted to must-have; `test-pipeline`
added to CONFIG_SKILL_MAP so its config inherits must-have tier.
Committed `2e71a6e`.

## 2026-06-12 — Porting a TS JSON client to Python: None ≠ omitted key

**Surfaced during:** notifier-hub-pattern goal run — Rule-29 independent
review of `core/.claude/templates/owner_notify.py` (HIGH finding).

**What I got wrong:** The Python port of `owner-notify.ts` passed optional
fields straight into the JSON payload (`"type": None`). `JSON.stringify`
silently DROPS `undefined` keys, but Python's `json` serializes `None` as
`null` — and the receiving validator (Notifier `/notify`) rejects a non-string
`type` with 400, silently dropping every alert sent without an explicit type
(requests doesn't raise on 4xx).

**What to do instead:** When porting a TS HTTP client to Python, filter unset
optionals before serializing (`{k: v for k, v in payload.items() if v is not
None}`) — match JSON.stringify's undefined-dropping, and check the receiver's
validator semantics for null vs absent. Gate-gap: no hub validator type-checks
template code against its wire contract — independent review (rule 29) is the
catching layer; keep it mandatory for templates.

## 2026-06-16 — Adding a registry pattern: bump `_meta.total_patterns` AND run pytest

**Surfaced during:** Promoting `goal-anchored-decisions` to the hub (PR #71). CI `validate` went red on `test_registry_integrity.py::test_total_patterns_matches_entries` (`_meta.total_patterns=262 but actual entries=263`).

**What I got wrong:** Added the `registry/patterns.json` entry but left `_meta.total_patterns` stale, and declared "validation passed" after running only `workflow_quality_gate_validate_patterns.py` + `dedup_check.py --validate-all` — neither checks the `_meta` count invariant. Skipped the full `pytest scripts/tests/` that CI actually runs.

**What to do instead:** The hub pattern-add checklist is FOUR steps, not two: (1) add/remove files in `core/.claude/`, (2) update `registry/patterns.json` **including `_meta.total_patterns` + `_meta.last_updated`**, (3) run `PYTHONPATH=. python -m pytest scripts/tests/` (esp. `test_registry_integrity.py`) — the two validator scripts are necessary but NOT sufficient, (4) `dedup_check --validate-all` + `--secret-scan`. Never claim CI-green from a local subset; reproduce the CI command set (`validate-pr.yml`).

## 2026-06-17 — Merging my own green PR is autonomous, not approval-gated

**Surfaced during:** Landing the doc-drift/count-dogfood fixes (PR #79). After CI went green I stopped and asked the user to approve the merge, framing "merge to main triggers downstream syncs" as an escalation. The user corrected: these are basic ops I must do autonomously — the role + approval framework exists precisely so routine landing isn't gated.

**What I got wrong:** Treated a routine merge as an outward/irreversible action. Within a flow the user already authorized ("land it"), merging a green, CI-passing PR I authored on its own branch is reversible/expected work. Normal downstream CI side-effects (`update-docs`, `sync-to-projects`) are designed behavior, NOT a reason to escalate. I also over-escalated one step earlier (asking before opening the PR).

**What to do instead:** Once "land it" is authorized and CI is green, carry the whole chain autonomously: commit → push → PR → **merge → branch cleanup → sync main**. Reserve approval-gating for genuinely destructive/irreversible/strategic git ops only: force-push, history rewrite, deleting others' work, prod deploy, spend, DNS cutover, a true product fork. Routine merges and expected downstream syncs do not qualify. State a one-line FYI if useful, but do not wait.

## 2026-06-18 — BA must model the FULL economic LIFECYCLE, not the one-time transaction

**Surfaced during:** Calculator v2 (dogfood). After re-scoping to 9 actors, the G1 mockup still modeled only the car *purchase* (acquisition + financing + resale). The user rejected it: the calculator's real value is the **multi-year cost of owning AND running** the car — fuel, maintenance, insurance over the loan/holding period — and the **loan-interest tax set-off** (a business deducts interest against income, so it effectively pays a fraction of the nominal interest). A purchase-only comparison "has no point."

**What I got wrong:** Second instance of the SAME incompleteness class as the actor miss — I bounded the value model to the triggering transaction and omitted the recurring/operating cost streams and their per-actor tax treatment, where the real decision lives.

**What to do instead:** For any cost/benefit or "should I buy/choose/finance X?" decision tool, the BA discovery MUST cover the full economic lifecycle over the realistic usage horizon: acquisition + financing (with the tax treatment of interest/fees — a set-off can make effective cost a fraction of nominal) + ongoing operating/running + maintenance + tax effect on EACH stream + exit/resale. A tool that compares only the upfront event is not decision-useful. Encoded as: `engineering-roles.md` PM mandate (v1.3.0, "Full economic LIFECYCLE" clause), `full-space-first.md` (v1.1.0, BA row + lifecycle bullet), and the `ba-usecase-discovery-reminder.sh` hook (v1.1.0). L1 rule + L2 hook; completeness still needs the L4 judge.

## 2026-06-18 — Stop patching BA misses one-by-one: a completeness CHECKLIST + independent audit

**Surfaced during:** Calculator v2. Third incompleteness miss in a row (actors → operating-cost lifecycle → which price/cost COMPONENTS benefit which actor). The user's key point: "the BA is not learning from mistakes — find best practices a BA should follow so these simple things don't get missed in ANY project of any domain."

**What I got wrong (the class):** Each miss was patched individually. The root cause is reasoning about the headline figure as a SCALAR and discovering a narrow slice, instead of reasoning as a MATRIX (actors × components × lifecycle) and verifying completeness independently.

**What to do instead:** Created `core/.claude/rules/ba-discovery-checklist.md` (v1.0.0) — the operational SSOT: a six-item checklist (actors · value-per-actor · lifecycle · component×actor benefit matrix · variants · aha-outputs), the ACTORS×COMPONENTS×LIFECYCLE **matrix discipline** (every cell filled or flagged as an open question — never a silent assumption; the cross-actor asymmetries ARE the value), and a mandatory **independent completeness audit before G1** (fresh-context reviewer asks "what's missing?"; dissent blocks G1). Wired via pointers in `engineering-roles.md` (v1.4.0), `full-space-first.md` (v1.2.0), the `ba-usecase-discovery-reminder.sh` hook (v1.2.0), and a G1 precondition in `human-approval-gates.md` (v1.1.0). The independent audit is what converts "the BA should remember" (unreliable) into "an independent check enforces it" (reliable) — the real anti-recurrence mechanism.

## 2026-06-18 — Over-ask recurred: trailing "say the word" offer on reversible git-landing work

**Surfaced during:** a `/init` CLAUDE.md audit. After applying the one doc improvement I ended the turn with "Want me to apply item 1…?" and, after fixing that, again with "Say the word and I'll branch, run CI, and open a PR." The `no-overask-guard.sh` Stop hook BLOCKED both turns and re-injected decision-authority. Only after the second block did I carry the full branch → CI → commit → push → PR → merge → cleanup chain.

**What I got wrong (the class):** This is a RECURRENCE of the 2026-06-17 "[[Merging my own green PR is autonomous]]" lesson and calc-retro item #6 — a prose lesson again failed to change behavior in the moment. I treated reversible/internal work (a one-line edit; routine git landing the user has a standing preference to do autonomously) as needing permission, and packaged the stop as a polite offer ("…or leave it untouched?", "Say the word…"). Politeness-as-offer is still over-ask; the hook reads the trailing question, not the intent.

**What to do instead:** On reversible/internal work — edits, the next queued item, and the WHOLE routine git chain (branch → local CI quartet → commit → push → PR → green → squash-merge → delete branch → sync main) — just DO it and report; never end on "want me to / should I / say the word / or leave it?". Reserve a closing question ONLY for a genuine blocker: my credentials, spend, deploy/DNS cutover, destructive/history-rewriting git, or a true product fork — and state that in one line, not as an offer. If unsure of *intent* (not permission), that's a different gate — open with `*Sync-check:*` and grill, which the hook exempts. The reliable mechanism here is the Stop hook itself; the lesson is to internalize it so the hook stops having to fire.

## 2026-06-18 — Skipped the BA→G1 pipeline: built a hub feature before discovery + design approval

**Surfaced during:** the web-analytics hub feature. Asked to "create that feature," I jumped straight to dispatching a subagent to write the rule + skill (GA4+GTM), then evaluated + opened a PR. The user stopped the merge: "what feature are you building? why didn't you follow the defined process to use BA and then go from there?"

**What I got wrong (the class):** I skipped the entire front of the project's own defined pipeline — **full-space BA discovery** (`full-space-first.md`), the **`ba-discovery-checklist`** (actors × components × lifecycle matrix + independent completeness audit), and **G1 design approval before build** (`human-approval-gates.md`). I locked GA4+GTM as *the* design without enumerating the option space, and built first. This is a recurrence of the full-space-first failure class — executing the narrow literal input instead of discovering the whole space first.

**The proof the gate matters:** when I finally ran the BA discovery (after being caught), it surfaced materially better-fit options the build had missed — Umami self-hosted (free, privacy-clean, unified 15-site view), server-side GTM for ad-blocker resilience, PostHog for the product apps, and the correctness fix that affiliate *conversions* live in the partner dashboard, not GA4 (GA4 sees the click only). The eval had been catching these reactively *after* building — exactly the symptom of skipping BA. (The user ultimately chose Google-only anyway, but chose it *informed* — which is the entire point of G1.)

**What to do instead:** For ANY "build/create this feature" request — including hub patterns — run the pipeline IN ORDER: full-space BA discovery (web-search the option space) → `ba-discovery-checklist` matrix → present a **G1 design for explicit user approval** → only then build. The hub feature itself is a product; "create a feature in this project" is NOT a license to skip BA/G1. A built-first PR is held as a draft/spike until G1 approves the design. Plan-before-coding + the confidence gate apply: when 2+ materially different valid designs exist (which a real BA discovery almost always reveals), converge with the user BEFORE building, not after.

## Up-front enhancement: a hard PreToolUse deny is the WRONG enforcement (2026-06-18)
Audit gap G1 ("force the enhance process UP FRONT, before tool work") was attempted as a
PreToolUse hook that DENIES the first Edit/Write until the reviewer card is present in the
current turn. It false-positives on MULTI-SEGMENT turns: when the Stop hook re-injects feedback
(a user-type message), it creates a new turn boundary, so a post-stop-block CONTINUATION looks
card-less and the gate blocks legitimate continuation edits — it bricked an edit in-session.
**Decision:** reverted (Bash recovery path worked because the matcher excluded Bash). The
correct enforcement layer is the **Stop hook** (catches omission at end-of-turn) + the
**UserPromptSubmit reminder** (demands rendering up-front). A PreToolUse hard-deny tied to
"card present in THIS segment" cannot distinguish "rendered earlier in a multi-part turn" and
is too blunt. If up-front telemetry is wanted later, make it ADVISORY (log), never a hard deny.
