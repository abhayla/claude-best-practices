Source: https://x.com/Mnilax/status/2074880097597689957
Captured: 2026-07-08

# Mnilax — "Build loops like Claude Code's creator (copy-paste setup inside)"

**Author:** Mnilax ([@Mnilax](https://x.com/Mnilax))
**Posted:** 2026-07-08 · **Engagement at capture:** 95 likes, 11 RTs, 3 replies, 16,002 views
**Format:** Single long-form X-native article (~8.6k chars).
**Nature:** **Conceptual loop explainer + personal 7-day case study.** Third/fourth-hand "Cherny's method" framing — no verifiable new mechanism. **Heaviest overlap yet with the existing loop-capture cluster.**

---

## What it says

Frames the post as "the setup the people who built Claude Code actually recommend": `/goal` + a separate verifier + worktree isolation + real stop conditions. Claims to have run this setup for 7 days against a real backlog: a flaky test suite went from failing to green, lint debt hit zero across ~40 files, a library got docstrings — "mostly while I slept."

**The four settings the author says make a loop reliable:**
1. **A separate verifier** — "the model that writes the code cannot be trusted to grade it." Anecdote: a migration-cycle writer reported "all tests pass" while a file had actually failed to import; the separate verifier caught it on the next cycle.
2. **A stop rule** — "success or a hard cap (iterations, dollars, no-progress)." Anecdote: adding "after 2 failed attempts on the same step, log it and move on" stopped the loop from chewing on one unsolvable item.
3. **A state file** — "an external note — done, failed, next — re-read at the top of every run." Anecdote: an overnight run resumed exactly where the prior run stopped instead of re-solving finished work.
4. **Worktree isolation** — parallel agents each get their own git checkout so they never collide. Anecdote: switching to worktree isolation turned a two-hour crawl on 40 files into 20 minutes with zero collisions.

**The numbers claimed:** ~340 cycles over 7 days, ~90 accepted changes, ~$210 in tokens, ~$2.30 per accepted change (~$1.10 on "productive cycles"), and "a separate verifier caught 14 completions the writer had wrongly marked done."

**The 4-part "is a loop worth it" test:** the task runs at least weekly; "done" is objectively checkable (test/diff/number); verifying is cheaper than doing; the agent has full context. Miss one, a plain prompt wins.

**Framing lines:** "A loop is cron plus a decision-maker plus a gate that says done." / "The unit of work is moving from the prompt you type to the loop you leave running." Closes with a "ten minutes to adapt the template" pitch and a Telegram plug (`t.me/aiXmnimi`) for weekly build notes.

---

## Relevance to this hub — LOW (near-total overlap with the already-captured loop cluster; no new mechanism)

Every mechanic here is already captured, in more authoritative or more detailed form, elsewhere in `docs/process-improvement/sources/`:

| Mnilax claim | Already-captured equivalent |
|---|---|
| "the setup Claude Code's creator recommends" / `/goal` + separate verifier + worktree + stop rule | Same "Cherny's method" framing, near-verbatim structure, in [0xChaseTM's note](2026-07-08-0xchasetm-build-your-own-loop-boris-method.md) (posted same day) |
| Separate verifier ("writer can't grade itself") | [ClaudeDevs official taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) — "second agent for review, fresh context, less biased" — first-party, higher authority; hub's `independent-test-verification.md` / `supervisor-verification.md` (maker≠checker) |
| Stop rule (iterations/dollars/no-progress cap) | [Raytar note](2026-06-23-raytar-stop-being-the-loop.md) 5-beats + ClaudeDevs "clear boundaries" token-usage list; hub's hard budgets + `/escalation-report` |
| State file (done/failed/next, re-read each run) | Raytar's "state file is the quiet hero"; hub's `.remember/` + scratchpad convention (`context-management.md`) |
| Worktree isolation for parallel agents | Hub's `loop-engineering:git-worktrees` skill + `agent-team-selection.md` (worktree = disk-only parallel isolation, cheaper than a full team) |
| 4-part "is a loop worth it" test | Raytar's identical when-not-to-build caveats; hub's YAGNI (rule 21) |
| "cron plus a decision-maker plus a gate" | Raytar: "a cron job runs a script; a loop runs Claude" — same distinction, same words almost |

**Nothing new survives the dedup pass.** The ~340-cycles/~90-changes/~$210 numbers and the "14 wrongly-marked-done completions" anecdote are the only Mnilax-specific artifacts, and they are unverifiable personal claims (no linked run logs, no repo) — **UNVERIFIED**, not to be cited as evidence. No copy-paste template, script, or config is actually included in the fetched text (the tweet references code blocks — settings, cron wiring, a Python headless loop — that did not resolve to distinct content in this capture; treat as absent rather than assume they contain something new).

The Boris Cherny "I don't prompt Claude anymore" quote lineage — now appearing across Raytar, 0xChaseTM, 0xCodila, and implicitly here — is **folklore by this point, fourth-hand at best**. Attribute to "widely circulated claim," never assert as fact.

**Action: none.** File for completeness (X-cluster coverage), take no doctrine action. If the hub ever wants a *second* concrete "separate verifier caught a false-done claim" anecdote alongside Raytar's fabricated-sources example, Mnilax's "skipped file that threw on import" line is a serviceable backup — but Raytar's is already the stronger teaching case.

**Cross-links:** [Raytar note](2026-06-23-raytar-stop-being-the-loop.md) (same Cherny framing, first in the cluster), [0xChaseTM note](2026-07-08-0xchasetm-build-your-own-loop-boris-method.md) (same-day, same "Cherny's method" framing), [ClaudeDevs official taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party, cite this instead), [0xCodila Karpathy/Bilevel note](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md).
