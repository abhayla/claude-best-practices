# Fable-5 high-value features — Tier 1 + Tier 2 execution plan (owner-approved 2026-07-14)

**Status:** APPROVED for build in a FRESH session (this session got bulky). Deduped against
everything shipped this session (see "Already have" at bottom). Discovery evidence: 3-scout scan
(official capability surface, fresh practitioner patterns, hub baseline) 2026-07-14.

**How to start the next session:** `/continue` (this plan + `.remember/remember.md` surface it) or
point directly at this file. Do items in the sequence below; each is its own CI-gated PR.

## Recommended SESSION SETUP (per `.claude/rules/model-routing.md` session-level routing)

This is **planned work with machine-checkable gates** → route to a **cheaper-driven session**, NOT
a Fable-driven one. Two good options:
- **Opus driver** (simplest), or
- **`/loop-engineering`** with `sonnet` maker + `opus` checker (maker≠checker, auto-verify each item).
Reserve Fable only for the one genuinely-novel design call if it arises (Feature B's checker-role
design). Feature A is mechanical → sonnet. This routing IS the hub's own doctrine; follow it.

## Recommended SEQUENCE (value-per-effort, dependency-aware)

1. **A** first — cheapest, highest-impact, no dependencies.
2. **C** — unblocks distribution; independent.
3. **B** — strategic (G5); benefits from A's schema being in place (cleaner checker signals).
4. **D**, **E**, **F** — Tier 2 follow-ons, any order.

---

## TIER 1

### A. Structured cross-agent finding schema (anti "agent poisoning")
- **What:** Force every agent that returns findings to T0 into a fixed schema —
  `Finding / Evidence / Impact / Fix / Priority(P0–P3, explicit criteria) / Confidence`. Strips
  inflammatory adjectives while preserving signal.
- **Why / goal:** Two real problems at once — (1) dramatic wording skews the orchestrator's severity
  read; (2) inflammatory vocabulary can trip Fable's safety classifier → silent Opus reroute mid-run
  (connects to our own preemptive-routing concern). Advances G5 orchestration reliability.
- **Fable strength exploited:** classifier sensitivity (avoid) + our heavy multi-agent orchestration.
- **Likely files:** `core/.claude/agents/code-reviewer-agent.md`, `.claude/agents/code-reviewer-agent.md`,
  `quality-gate-evaluator-agent.md`, `.claude/agents/security-auditor-agent`/core copy,
  `test-failure-analyzer-agent.md` — update each "## Output Format" section to the schema. Consider a
  new short rule `core/.claude/rules/agent-finding-schema.md` (`# Scope: global`) as the SSOT the agents
  point to (DRY — don't copy the schema into each). Dual-home + registry hashes for any registered edits.
- **Effort:** LOW-MED. **Verify:** dispatch a code-reviewer on a trivial issue, confirm output is schema-shaped
  and free of severity-inflating adjectives; run agent-evaluator if scenarios exist.
- **Source:** limitededitionjonathan "Your Agents Are Poisoning Each Other" (2026-07-04) [single-source but
  mechanistically sound + directly testable].

### B. Fable as the adversarial CHECKER in the trust-score loop (G5 accelerator)
- **What:** Wire a cheaper *maker* + **Fable *checker*** on high-stakes `loop-engineering` gates, so the
  trust-score calibration ledger (`trust-score/ledgers/atlas.jsonl`) accrues HIGHER-quality verification
  signals. Today Fable is reserved for our own design sessions; no loop uses it as the checker role.
- **Why / goal:** G5 (autonomous machine, ~50%, the drifting goal) is DoD-gated on the ledger reaching ≥30
  real entries — better checker signals = faster, more-trustworthy graduation.
- **Fable strength exploited:** first-shot correctness + high bug-finding recall (outside cyber domains).
- **Likely files:** `core/.claude/skills/loop-engineering/SKILL.md` (STEP 5 VERIFY — add a Fable-checker
  option on high-stakes gates), `.claude/rules/model-routing.md` (a checker-role routing line),
  `docs/specs/loop-engineering-spec.md`. Design the "when is a gate high-stakes enough to spend Fable"
  predicate — THIS is the one place to consider a Fable-driven design call.
- **Effort:** MED. **Verify:** run one real loop cycle with the Fable-checker arm; confirm a ledger entry
  accrues and the maker≠checker invariant holds. Watch cost via `cost_ledger.py --report`.
- **Source:** hub baseline goal-gap analysis (this session) + Fable capability profile.

### C. Promote Fable routing/refusal discipline to distributable `core/` (G6 gap)
- **What:** Our model-routing tiers, effort dial, refusal-fallback, preemptive routing live **hub-only**
  (`.claude/rules/model-routing.md` + `docs/governance/refusal-fallback-playbook.md`). Downstream projects
  installing our plugins get NONE of it. Promote to `core/.claude/rules/` (genericized) or fold into a plugin.
- **Why / goal:** real distribution gap; directly serves G6 (installable cross-project capability).
- **Likely files:** new `core/.claude/rules/model-routing.md` (genericize: strip hub-only paths/session
  facts, keep the tier table + effort dial + refusal-fallback + preemptive routing), registry entry + hash +
  docs regen; classify in `config/dual-home-resources.yml`. Decide rule-vs-plugin (a rule is simpler; a
  `cbp-fable-routing` plugin is the fuller G6 play). Follow `/promote-to-core` recipe.
- **Effort:** MED. **Verify:** provision into a scratch/downstream repo, confirm the routing rule loads.
- **Source:** hub baseline goal-gap analysis (this session).

---

## TIER 2

### D. High-res vision + crop-tool verification upgrade (CC-native)
- **What:** Add a crop-then-zoom sub-skill to the screenshot-verification flow so a verifier zooms into
  small-text / dense-table / overlapping regions instead of trusting a full-page high-res read.
- **Why:** Fable's high-res vision tier has a documented accuracy drop on small fonts/dense tables;
  Anthropic's own fix is the crop-tool cookbook pattern. Sharpens correctness of visual verification.
- **Fable strength:** upgraded high-res vision (2576px/4784 visual-token tier) — CC-native, auto-on.
- **Likely files:** a new sub-skill under the verification flow; cross-ref `core/.claude/rules/web-deploy-readiness.md`
  (390/768/1280 gate), `supervisor-verification.md` "drive the UI" gate. The crop tool itself is a custom
  tool you implement (Anthropic cookbook `multimodal-crop-tool`) — CC ships no built-in crop tool (unverified).
- **Effort:** MED. **Verify:** feed a screenshot with a small-font region, confirm crop-then-read beats
  full-page read on that region.
- **Source:** official capability scan — Vision doc + crop-tool cookbook.

### E. Mechanically-gated requirements ledger
- **What:** A disk-persisted requirement checklist enforced by HOOKS — a PreToolUse "spawn guard" that blocks
  large subagent dispatch unless a ledger exists, and a Stop "close guard" that blocks session close with
  unchecked ledger items. We have `.claude/tasks/todo.md` + `subagent-governance-inject.sh` but no MECHANICAL gate.
- **Why:** our own `rule-writing-meta.md` prefers a deterministic gate over prose; Fable's long-horizon
  autonomy makes dropped requirements across context windows a real risk. Advances G5 reliability.
- **Likely files:** new hook(s) in `.claude/hooks/` (+ `core/` for distribution), wired in `settings.json`;
  a ledger convention doc. Model on the `fable5-orchestrator` LEDGER.md + spawn/close-guard pattern.
- **Effort:** MED. **Verify:** attempt a big dispatch with no ledger → blocked; attempt session close with an
  unchecked item → blocked. Use the hook-transcript-fixture-test skill.
- **Source:** Rylaa/fable5-orchestrator (practitioner scan) [single-source].

### F. Deterministic "second loop" ship-gate (AC/DC pattern)
- **What:** Make the FINAL ship gate a **deterministic static-analysis pass** (same verdict every run),
  explicitly distinct from the probabilistic maker self-check AND the independent-agent check. Worked
  example: Fable's self-tests passed a SQL-injection that deterministic taint-analysis caught.
- **Why:** sharpens our maker≠checker doctrine — the last gate should be deterministic, not another
  probabilistic agent. Partly covered by `independent-test-verification.md`; the new bit is the
  deterministic-static-gate emphasis.
- **Likely files:** refine `core/.claude/rules/supervisor-verification.md` / `independent-test-verification.md`
  (add the deterministic-outer-loop clause); wire a static-analysis step into the ship gate where a stack has one.
- **Effort:** LOW-MED (largely a rule refinement + wiring a static gate). Mostly-dedup — check what's already
  covered before adding.
- **Source:** Sonar "Why Fable 5 Still Needs a Second Loop" (2026-06-11) [single-source].

---

## Already have (do NOT re-propose)
operating-manual plugin (manual + distilled-core + `/model-parity-test` + eval battery); model-routing
(tiers, effort dial, preemptive routing, refusal-fallback, session routing); refusal-fallback playbook
(task budgets, send_to_user, sticky routing, cache facts); loop-engineering spec §3.9 (Fable runtime
hardening); cost ledger (per-project + verified $10/$50 Fable rates); trust-score subsystem;
untrusted-content-handling rule; discovery-issue injection guard.

## Deferred (Tier 3 — measure/awareness, NOT in this batch)
G re-run parity-test vs post-July-1 Fable (measure); H 1M-context whole-repo scan (measure-first, rule 22);
I add "agent view"+"dynamic workflows" to agent-team-selection.md (doc); J package raw-API primitives
(memory tool/code-exec/PTC/context-editing) as a downstream-agent-builder plugin (G6, product-repo-facing);
K reuse /model-parity-test as a G6 pre-graduation gate. Owner said "ignore" the security P2 batch (#9–13).
