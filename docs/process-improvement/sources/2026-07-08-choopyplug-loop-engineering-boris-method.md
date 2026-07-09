Source: https://x.com/choopyplug1/status/2074879612765503774
Captured: 2026-07-08

# choopyplug1 — "Loop Engineering: the Boris Cherny Method"

**Author:** choopyplug1 ([@choopyplug1](https://x.com/choopyplug1))
**Posted:** 2026-07-08 · **Engagement at capture:** 18 likes, 1 RT, 6,633 views
**Format:** Single long-form X-native article, five numbered parts (~10.5k chars).
**Nature:** **Conceptual loop explainer + numbered build tutorial + "honest part" failure-modes section.** One second-hand attribution to verify (Boris Cherny "I don't prompt Claude anymore... My job is to write loops"). **Near-total overlap with the existing loop-capture cluster** — opens on the identical Cherny quote already captured via Raytar and 0xChaseTM, and restates the same maker/checker, state-file, worktree, and heartbeat mechanics as the first-party ClaudeDevs note. Captured for completeness; LOW incremental signal.

---

## What it says

**Part 1 — What a loop is:** a prompt is one instruction with a human deciding what's next each time; a loop is a goal the AI keeps working toward without per-step prompting. Opens on the Cherny quote (attributed, unsourced in-article): *"I don't prompt Claude anymore. I have loops running that prompt Claude and figuring out what to do. My job is to write loops."*

**Part 2 — The four-condition test for whether a loop is worth building:** (conditions shown only as an image in the source, not spelled out in text — inferred from surrounding prose: the task repeats, verification is machine-checkable, the token budget can absorb waste, and the agent has real tool access). Good first loops: CI failure triage, dependency bumps, lint-and-fix passes, flaky-test reproduction, issue-to-PR drafts on code with strong tests. Skip for now: architecture rewrites, auth/payments, production deploys, anything where "done" is a judgment call.

**Part 3 — The build, ten numbered steps, each with a copyable prompt (per source, images not reproduced here):**
1. Write the goal, not the next prompt — `/goal` sets a persistent completion condition; a smaller separate model checks it after every turn.
2. Separate the maker from the checker — a second pass, different instructions, sole job is finding what's wrong (self-preferential bias means the author is "too generous" grading its own work).
3. Give it memory that survives the session — CLAUDE.md read at every session start; write the lesson into the file, don't just fix it in chat.
4. Keep a state file (STATE.md in-repo, or an external system like Linear/GitHub Issues/a DB) so tomorrow's run resumes instead of restarting cold; pair with a standing VISION.md spec for long-running loops (state = where it is, spec = where it's going).
5. Isolate parallel agents with git worktrees — Claude Code exposes `isolation: worktree` on subagents; Codex has native worktree support; review bandwidth, not mechanics, caps how many agents you can run (start with two, not ten).
6. Connect it to real tools via MCP — GitHub (biggest day-one win), Linear/Jira, Slack, Sentry, ranked by payback speed.
7. Add the heartbeat — `/loop` re-runs on a cadence; `/goal` runs until a condition is true, checked by a separate model so the maker can't grade its own stop condition.
8. Turn every verifier rejection into a permanent rule — distill the catch into a hard rule written into the file the loop reads; "the honest version of self-learning: the model isn't retraining, the system around it is getting smarter."
9. Scale from one loop to a small fleet — Cherny reportedly runs several loops concurrently (architectural improvements, deduplicating abstractions); the metric that matters at fleet scale is **cost per accepted change** — below 50% acceptance, the loop costs more than it saves.
10. Promote the loop to a background agent — point a stable, skill-backed loop at a trigger (schedule/webhook/file-drop); the only human left is the question set and the decision on the answer.

**Part 4 — Where this goes wrong (failure modes):** token costs compound (loops re-read/retry regardless of whether the run ships anything); loops fail quietly without a hard stop condition; an unattended loop with merge/write access is an unattended attack surface needing scheduled permission re-checks, not one-time; comprehension debt compounds if you stop reading diffs. Named mistakes: no independent gate, one agent writing-and-checking (self-preferential bias), no state file, vague stop conditions ("looks good"), no token budget cap (ambitious loops burn 5-10x expected), loops applied to judgment calls (architecture/auth/payments), not reading diffs.

**Part 5 — What Cherny thinks comes next (reported, unsourced):** asked what humans stay uniquely good at, he reportedly said "values" — teaching a system what to care about, not code/design/product sense. Reportedly runs "hundreds of Claude instances" monitoring Twitter/GitHub/Slack surfacing product ideas, most bad today, expected mostly good "within months." Personal arc as reported: late 2024 Claude wrote 10-20% of his code, mid-2025 he uninstalled his IDE, 2026 he doesn't prompt Claude at all — he designs the systems that do.

**Conclusion:** most developers don't need a loop yet — only once the task repeats, verification is automated, the budget absorbs waste, and real tools exist. Start small: one heartbeat, one skill, one state file, one gate; get one manual run reliable, turn it into a skill, wrap it in a loop, schedule it, in that order. "Write the goal, not the prompt. Separate the checker from the maker. Give it memory. Then get out of the way."

---

## Relevance to this hub — LOW (redundant with the cluster, confirmed against Raytar/0xChaseTM/ClaudeDevs; no new mechanism)

Every mechanic here is already captured, in more depth and/or with a first-party citation, by the existing loop cluster:

| choopyplug1 point | Existing hub mapping |
|---|---|
| Machine-checkable finish line / four-condition "should I loop this" test | `goals.yml` DoDs; trust-score `threshold` + `hard_gates`; same four-condition framing already implicit in 0xChaseTM's capture |
| Separate maker vs. checker, self-preferential bias | `independent-test-verification.md` + `supervisor-verification.md` — same claim already surfaced via [ClaudeDevs](2026-07-06-claudedevs-getting-started-with-loops.md) and [0xChaseTM](2026-07-08-0xchasetm-build-your-own-loop-boris-method.md) (there cited as a ~3x quality claim) |
| CLAUDE.md / state file / VISION.md persistent memory | `CLAUDE.md` self-improving-rules convention; `.remember/` handoff log; `context-management.md` rule 6 (state-on-disk survival) |
| Git worktree isolation for parallel agents | `agent-team-selection.md` (worktree = disk-only parallel-edit isolation tier) + `git-branch-lifecycle` skill `work <name>` worktree mode |
| MCP tool connectors (GitHub/Linear/Slack/Sentry) ranked by payback | Already the hub's own posture — GitHub via `gh`, Notifier gateway for Slack/WhatsApp-equivalent alerts (`notifier-integration.md`) |
| `/goal` + `/loop` heartbeat, verifier-rejection → permanent rule | `loop-engineering` plugin (DISCOVER→PLAN→EXECUTE→VERIFY→SHIP) + native `/goal`/`/loop` primitives, already mapped in the ClaudeDevs capture's adoption table; rule 5 self-improving-rules already codifies "turn a correction into a rule" |
| Fleet-scale "cost per accepted change" < 50% kill metric | Novel framing detail, but not hub-actionable today — no fleet of concurrent autonomous loops exists yet to meter |
| Cherny's personal-workflow anecdote (phone-only, "hundreds of instances," values framing) | Anecdotal color, no new hub-actionable mechanism |

**No genuinely new angle survives comparison with the cluster.** The ten-step build sequence and four "honest part" failure modes restate ground already covered by [Raytar](2026-06-23-raytar-stop-being-the-loop.md) (same Cherny quote, sharper example), [0xChaseTM](2026-07-08-0xchasetm-build-your-own-loop-boris-method.md) (same walkthrough shape), and [ClaudeDevs](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party authoritative source). The only mildly distinct item — "cost per accepted change" as a fleet-scale kill metric — is a framing nuance, not a new primitive, and doesn't warrant a doctrine change on its own.

**Attribution note:** the Boris Cherny quotes and figures here ("I don't prompt Claude anymore... My job is to write loops," the 10-20%→IDE-uninstall→zero-prompting arc, "hundreds of instances," the values framing) are second-hand, un-sourced-in-article claims. This is now the **fourth** capture repeating this same Cherny quote lineage (Raytar, 0xCodila, 0xChaseTM, this one) — treat as recurring folklore around a real Anthropic-team member until a primary source (his own post or talk) is located. Any Fable/model-capability claims implied by "the ceiling is not the model, it's the loop" are likewise unverified and not to be repeated as fact.

**Action:** no action — confirmation-only capture, redundant with the Raytar/0xChaseTM/ClaudeDevs cluster. Do not duplicate anything into `loop-engineering-spec.md` from this source.

**Cross-links:** [Raytar — Stop Being the Loop](2026-06-23-raytar-stop-being-the-loop.md) (same Cherny quote, sharper example), [0xChaseTM — How To Build Your Own Loop](2026-07-08-0xchasetm-build-your-own-loop-boris-method.md) (same walkthrough shape, captured same day), [ClaudeDevs — Getting Started with Loops](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party authoritative source, cite this one), [0xCodila — Karpathy/Bilevel loop](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md).
