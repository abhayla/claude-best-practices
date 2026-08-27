# Capability Advisor — make every project use the right Claude Code features, with zero commands to remember

Status: DRAFT v1 for independent review (2026-08-27). Owner: Abhay. Driver: Fable session.
Branch: `feature-utilization-meter` (worktree `D:/Abhay/GetWorkDone/wt-check/cbp-feature-meter`).

## 1. Problem (owner, 2026-08-27, verbatim intent)

"Whenever I work on a project I do not utilize Claude Code's features at their fullest — right skills, right agents, splitting work across them. I keep using the features I know. Many features exist that I don't know about. Fix this, fully autonomously, for new and existing projects. The user may forget commands — nothing should depend on remembering a command."

## 2. Evidence (scripts/feature_utilization.py, 30 days to 2026-08-27, 1,050 transcripts, corrected after review)

- Owner hands-on: 590 sessions. Used **19 / 219 installed skills, 4 / 47 installed agents (8.6%)**.
- Plan mode: 16 exits in 3 sessions. `Workflow`: 2 calls. `EnterWorktree`: 0 owner. `CronCreate`: 10.
- Agent dispatches: 241 owner, of which ~190 `general-purpose`. Specialist review/test/security agents: ~5 total.
- Never used: all 17 `cbp-build-test-workflows` skills, all 16 `cbp-workflows`, all 12 `loop-engineering`, all 30 `vercel`, 11 `postman`, 8 `cloudflare`, 6 `desktop-commander`, 2 `supabase`, 42 hub-local skills.
- Duplicates: `fix-loop`, `writing-plans`, `brainstorm`, `systematic-debugging`, `code-reviewer-agent` each exist in 3–4 namespaces. All at zero.
- Browser is the most-used feature by far (Chrome MCP 1,351 + Playwright 793 calls).
- Root cause: not "unknown features" — they are installed. There is **no selection step** at the moment of work, and the option set (220 descriptions) is too large to pick from. Prose rules telling Claude to "use skills" have been tried in this hub for 3 months without converging (559 enhance-misses, 840 stop-hook auto-continues).

## 3. Approach (Musk algorithm order: requirement → delete → simplify → accelerate → automate)

**Requirement (fixed):** every task gets the *cheapest feature set that measurably improves outcome*, chosen without the owner doing anything. NOT "use everything".

### Part A — Delete (data-backed, reversible)
- Uninstall plugins with zero usage in 30 days AND no matching stack in any registered repo (`D:\Abhay\GetWorkDone\settings.json → repo_registry`): vercel, postman, cloudflare, supabase, desktop-commander, pydantic-ai, telegram (verify each against the registry before removal; keep anything a registered repo's stack needs even if unused).
- Collapse duplicate skills/agents to ONE home each (hub decision: plugin copy wins; hub-local + `core/` copies become thin pointers or are removed), so a name resolves to exactly one thing.
- Expected: ~65–80 fewer skill descriptions in context per turn. Reversal: `/plugin install`.

### Part B — The Capability Plan as an auto-loaded rule file
- Artifact: `<project>/.claude/rules/capability-plan.md`, `# Scope: global`, ≤ 40 lines: a **decision table** `task shape → steps (skill/agent/primitive) → gate`, plus "missing → built", "stale → updated", "hidden for this project".
- Claude Code auto-loads `.claude/rules/*.md` — no command, no hook is needed to APPLY it.
- Generator: `scripts/capability_advisor.py` (hub) + a thin skill wrapper `/capability-plan` for manual re-run only. Inputs: (1) project facts — stack detection reused from `scripts/dependency_detection.py` + `recommend.py --local`, existing `.claude/` contents, repo size, CI presence, deploy scripts; (2) `docs/claude-references/capability-catalogue-<date>.md` (what exists); (3) `feature_utilization.py --json` (what the owner actually uses; what's installed); (4) the project's `CLAUDE.md`/rules. Output = the rule file + a `capability-plan.json` sidecar (machine-readable rows for the Stop-hook telemetry).
- Row synthesis is a Sonnet call (`claude -p`, effort low) over a fixed prompt + the inputs; the deterministic parts (inventory, stack, staleness) are Python. Cost: cents per project per week.
- **Missing skill/agent → built immediately** (owner-delegated, reversible): the advisor emits a contract per missing item and dispatches `/synthesize-project --local` / `skill-author-agent` in that project's worktree; lands via branch + CI. Stale → updated the same way. Both recorded in the plan file with the PR link.

### Part C — Zero-command automation (hooks, user-level so every project gets it)
1. **SessionStart (user-level `~/.claude/settings.json`)** — `capability-plan-refresh.py`: skip if a GWD fleet marker is present; else if the rule file is missing, older than 7 days, or the project fingerprint changed (hash of manifests + `.claude/` tree + plugin-cache listing) → run the advisor **in the background** (detached, ≤ 2 min, writes atomically), and print the current plan's rows (or "generating — shown next session") as `additionalContext` in the start banner. Also ticks `feature_utilization.py --json --days 30` weekly (cached; cold run ~51 s so never inline) and re-runs the catalogue scout (`/review-new-claude-features` in headless mode) when the catalogue is > 30 days old.
2. **Apply** — no hook; rule file in context.
3. **Stop (telemetry only, never blocks)** — `capability-plan-adherence.py`: classify the turn's task shape (keyword/size heuristic over the user prompt), look up the plan row, check the transcript tail for the row's skill/agent/primitive names, append one JSONL line `{project, session, shape, row, expected[], used[], adhered}` to `~/.claude/.capability-adherence.jsonl`. Zero cost (no model call).
4. **Escalate by data** — weekly, the meter prints **adherence % per row**. A row < 50% for 2 consecutive weeks → a PreToolUse gate for that row is proposed as a contract (e.g. "3rd file edit without a plan artefact → block with the row text"). Gates are added one at a time, owner-visible in the plan file, never upfront.

### Part D — Measure (the only success criterion)
- `feature_utilization.py` gains a "plan adherence" section reading the adherence JSONL. Weekly line in the SessionStart banner: `capability: used X/Y recommended rows (adherence Z%); specialist agents N; plan-mode sessions M`.
- Targets: adherence ≥ 70% by 4 weeks; specialist-agent share of dispatches ≥ 30%; owner skill coverage of the *plan's* rows (not of all installed) ≥ 80%. Miss → RCA of the plan rows, not more prose.

## 4. Non-goals
- No new always-on prose rule. No blocking hook until data demands it. No "use everything".
- Never touches get-work-done fleet-core (frozen); fleet workers skip all of this.
- Does not replace `recommend.py` / `/synthesize-project` / `/review-new-claude-features` — it calls them.

## 5. Build order & size
1. Land the meter + catalogue (done, reviewed, 23 tests). 
2. `capability_advisor.py` + tests + `/capability-plan` wrapper (hub). Sonnet implements, Opus reviews.
3. Hooks: `capability-plan-refresh.py` (SessionStart) + `capability-plan-adherence.py` (Stop) in `D:\Abhay\GetWorkDone\hooks\` (where the other user-level hooks live), wired in `~/.claude/settings.json`; red-then-green self-tests like the existing hooks.
4. Part A deletions (after 2–3 lands, with the registry check).
5. First real plans: this hub, IPODhan, gorefer. Verify banners appear with zero commands typed.
6. Week-1 adherence readout → first gate decision.

## 6. Risks (honest)
- Adherence to a rule file is not guaranteed; it is measured and gated where it fails. Hub history says prose alone ≈ 8%; a 10-row project-specific table is a different regime but unproven — that is what Part D exists for.
- Task-shape classification in the Stop hook is a heuristic; misclassification shows as noisy adherence. Mitigation: log the guess so it can be audited; accept ±10% noise.
- SessionStart latency: everything heavy is detached; banner reads a cached file only.
- Owner/fleet split in the meter is a floor (workers inside app repos are indistinguishable by slug); a session marker from the fleet would fix it — out of scope (fleet-core frozen).
- Windows: hooks are Python (not bash), as the existing user-level hooks are.
