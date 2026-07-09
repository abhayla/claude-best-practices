Source: https://x.com/phosphenq/status/2068468824421364103
Captured: 2026-07-09

# phosphenq — "Loop Engineering: Build an AI That Codes While You Sleep"

**Author:** phosphenq ([@phosphenq](https://x.com/phosphenq))
**Posted:** 2026-06-20 · **Engagement at capture:** 945 likes, 132 RTs, 825,672 views
**Format:** Single long-form X-native article (~9.7k chars).
**Nature:** **Conceptual loop explainer.** Opens on a second-hand Boris Cherny anecdote (259 PRs in a month, "didn't open an editor"), builds a "six pieces + one question" framework, then spends roughly half the piece on failure modes and cost discipline. **Heavy overlap with the existing loop-capture cluster** — captured for completeness; the failure-mode taxonomy and cost framing are the only things not already on file verbatim.

---

## What it says

Opens with Boris Cherny shipping 259 PRs in a month without opening an editor, and Peter Steinberger's line ("You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents" — 8M+ views) as the thesis. Immediately pairs it with a cautionary anecdote: an unwatched loop ran 11 days and burned $47,000 before anyone noticed. Central question: **"does it converge on something true, or is it just an expensive random walk?"**

**Six pieces of a working loop:**
1. **State** — the only thing the next run inherits; a `STATUS.md` or Linear board holding done/in-progress/next/never-touch. "You are judged by the note waiting on your desk at nine."
2. **Automations** — what makes it a loop vs. a one-off run. Maps Codex app's Automations tab (repo+prompt+cadence, triage inbox) against Claude Code's primitives, and is explicit that popular write-ups get this wrong: **`/loop` is a skill** (re-runs a prompt on a cadence, session must stay open) vs. **Routines** (`/schedule`, 1-hour minimum, survive a closed laptop — no local crontab). Singles out **`/goal`** as "the one worth learning": runs until a written condition is true, checked each turn by a separate, smaller model — "the agent that wrote the code does not get to grade it." Contract-quality stop conditions only ("all tests in test/auth pass," not "make it better").
3. **Worktrees** — the wall between parallel agents (separate working dir, same history). Caveat: worktrees remove file collisions, not the review bottleneck — "however many agents you start, your own review bandwidth decides how many you can trust."
4. **Skills** — intent written once, read every run, so the agent stops guessing; same folder+SKILL.md format on both tools; flat literal descriptions trigger better than clever ones.
5. **Connectors** — MCP-based; the line between "here is the fix" and a loop that opens the PR, links the ticket, reports green.
6. **Sub-agents** — maker≠checker as the "highest-value move in any loop": one explores, one implements, one verifies against spec; ties this directly back to `/goal`'s separate-model check.

**Composite example:** morning-scheduled automation → triage skill reads CI/issues/commits → writes findings to `STATUS.md` → worktree-isolated draft-agent + review-agent pair per finding → connectors open PR/update ticket → unhandled items wait in a triage inbox. "You designed it once. You prompted none of it."

**Failure-mode taxonomy (the piece's most distinct content):** four named death modes — **Runaway recursion** (two agents feed each other forever; cure = step cap + budget ceiling — this is explicitly the mechanism behind the $47k/11-day story); **Silent death** (hits a full context window, keeps trying to resume into the same wall while "still looking alive"; cure = heartbeat + fresh context per phase); **The random walk** (no verifiable stop condition, drifts instead of converging; "a passing test suite is a fixpoint... 'looks done' is not one"); **Comprehension debt** (ship code faster than you understand it, "you stop being the engineer and become a rubber stamp"; cure = a human-read gate the loop is never allowed to skip).

**Cost honesty:** explicitly contrasts Steinberger's ~$1.3M/month hundred-agent fleet ("sponsored" by OpenAI employing him) against a $20–$200 personal plan, where "the loop that pays off is small, capped, and pointed at one dull job, not a swarm." Closing prescription: "brakes before horsepower" — scope by blast radius (repos/branches/dollars/step-count) before scoping by task.

---

## Relevance to this hub — LOW

Every mechanic maps to a pattern the hub already ships, mostly via `loop-engineering` (`core/.claude/skills/loop-engineering/SKILL.md`, spec `docs/specs/loop-engineering-spec.md`) and adjacent doctrine:

| Article concept | Hub equivalent |
|---|---|
| State file (`STATUS.md`) as "the quiet hero" | `.remember/` (`now.md`/`recent.md`/`archive.md`) + scratchpad discipline (`context-management.md` rule 3/6) |
| `/goal` — separate smaller model checks done-ness each turn | maker≠checker gating in `independent-test-verification.md` / `supervisor-verification.md`; DoD-style stop conditions in `goals.yml` |
| Sub-agents, maker vs. checker | `code-reviewer-agent`, `pre-git-merge-checker-agent`, and the model-routing tiering in `model-routing.md` (checker MAY differ from maker) |
| Worktrees for parallel isolation | `git-branch-lifecycle` `work` mode; `agent-team-selection.md` (worktree = disk-only isolation, cheaper than a team) |
| Skills as written-once intent | the hub's entire skill-authoring model (`writing-skills`, `core/.claude/skills/`) |
| Connectors / MCP | already the hub's standard tool-access layer |
| Runaway recursion / budget caps | `loop-engineering` hard budgets + fix-loop/debugging-loop iteration limits |
| Comprehension debt / human-read gate | `plan-before-coding.md`, human-approval gates in BA/PM discovery |

**No new mechanism found.** The four-part failure taxonomy (runaway recursion, silent death, random walk, comprehension debt) is a tidier *naming* than anything on file, but the underlying cures (step caps, heartbeats/fresh-context, verifiable stop conditions, human-read gates) are all already implemented, not just described. The `/loop` vs. Routines (`/schedule`) distinction is accurate and matches the hub's own skill inventory (both are separate skills in this session's tool list) — nothing to correct.

**Unverified claims (flag, don't assert):** the Boris Cherny "259 PRs in a month, never opened an editor" anecdote is second-hand and unsourced in the article itself — same pattern as the Cherny quote already flagged unverified in the [Raytar capture](2026-06-23-raytar-stop-being-the-loop.md) ("I don't prompt Claude anymore"). Two independent captures now carry a Cherny attribution — still treat as reported claim, not verified fact, until a primary source (talk, blog, tweet from Cherny himself) is located. The Peter Steinberger "$1.3M/month, 100-agent fleet" figure and the "$47,000 / 11 days" runaway-loop cost are also unverified third-party numbers — no primary source given in the article.

**Verdict: no action.** File for corroboration only. If the hub ever writes a dedicated "why loops fail" section in `loop-engineering-spec.md`, the four-death-mode naming here is a clean reference point — otherwise this adds no capability, pattern, or correction the hub doesn't already have.

**Cross-links (loop-capture cluster):** [ClaudeDevs first-party taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md), [0xCodila Karpathy/Bilevel](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md), [Raytar — Stop Being the Loop](2026-06-23-raytar-stop-being-the-loop.md), [hanako while-you-sleep](2026-06-13-claude-loops-while-you-sleep.md), [Andrew Ng 3 loops](2026-06-30-andrew-ng-3-product-development-loops.md).
