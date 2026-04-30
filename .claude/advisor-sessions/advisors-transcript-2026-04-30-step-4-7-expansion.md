# Five Advisors Transcript — 2026-04-30

**Topic:** Should the /prompt-auto-enhance STEP 4.7 Execution Mode Selection Gate be expanded from 3 prompt shapes (decision/planning/exploration) to 8 (adding implementation, bug-fix, review/audit, documentation, authoring)?

**Invocation:** Direct (`/five-advisors`) — workspace context-enrichment skipped because session already had full context loaded (CLAUDE.md, both SKILL.md files, available-skills list, prior design turn from same session).

---

## Original Question

The user proposed adding 5 NEW shape categories to STEP 4.7 with scenario-mapped skill suggestions. Asked the council whether to proceed, modify, or reject in favor of an alternative approach.

## Framed Question (presented to all 5 advisors)

The /prompt-auto-enhance skill has a STEP 4.7 "Execution Mode Selection Gate" — an ignorable post-strengthening menu that lets the user pick how to execute the prompt. v3.1.1 covers 3 prompt shapes (decision, planning, exploration) with 4 execution options + "Execute directly".

**Proposed expansion: add 5 NEW shape categories to the menu:**
- Implementation ("implement", "add feature", "build X" + multi-file or framework-specific) → offer /implement, /tdd, /development-loop, plan mode
- Bug-fix ("fix", "broken", "error", failing test) → offer /fix-loop, /debugging-loop, /systematic-debugging, /fix-issue
- Review/Audit ("review" / "audit" + scope) → offer /code-review-workflow, /security-review, /security-audit
- Documentation ("document", "write docs/README") → offer /documentation-workflow
- Authoring ("create skill/agent/rule") → offer /writing-skills, /claude-guardian, /pattern-quality

**Trigger:** conservative — fire only when complexity signal present.

**Constraints:** must not duplicate /skill-master, menu must stay rare-and-relevant (Hick's law), each option must offer something beyond direct execution, per-shape cap of 5, "Execute directly" always silent default. Existing anti-pattern in SKILL.md against menus on direct implementation/bug-fix would need revision.

**At stake:** if right, scenario-aware execution choice across all common Claude Code work. If wrong, menu becomes noise → trust in entire auto-enhance pipeline erodes. Design replicates downstream via /synthesize-project.

---

## Anonymization Mapping (revealed at end)

| Letter | Advisor |
|--------|---------|
| A | The Outsider |
| B | The Executor |
| C | The First Principles Thinker |
| D | The Contrarian |
| E | The Expansionist |

---

## STEP 2 — Advisor Responses

### The Contrarian

Reject as proposed. The expansion is rationalizing scope creep into a doctrine.

**The fatal flaw:** you are inverting your own anti-pattern, not retiring it. The current SKILL.md says menus on direct implementation/bug-fix prompts add friction. The proposal's response is "make them shapes instead of suppressors." That is not new evidence — that is renaming the problem. Where is the data that users actually wanted a menu on "fix the failing test"? If the only justification is "Implementation and Bug-fix are common shapes," you have proven the opposite of your case: common shapes are exactly where friction compounds.

**The load-bearing assumption that's shaky:** "complexity signal" as a gate. Multi-file, framework-specific, and "stakes" are not orthogonal — almost every non-trivial prompt hits at least one. Your conservative gate will fire on most real work within a week. You will end up with a menu on every prompt, which is the failure mode you claim to be preventing.

**The hidden cost no one is pricing:** five new shapes means five new ways the shape detector can misclassify. A prompt like "fix the architecture review doc for the auth bug" hits Bug-fix, Review, and Documentation. What wins? You haven't specified. Ambiguous classification on a menu that interrupts execution is worse than no menu.

**What you're avoiding:** if `/skill-master` already routes, why does auto-enhance need a parallel menu? "Separate router skill" is an assertion, not a justification. Two routers competing for the same decision is exactly how trust erodes.

**Counter-proposal:** ship Implementation only, behind telemetry. If acceptance rate beats 30% over 50 fires, expand. Otherwise the menu dies and you've saved four shapes worth of replication damage downstream.

### The First Principles Thinker

Strip the proposal down: you're adding a menu so users can pick an execution skill. But why does the user need to pick? Because the auto-enhance pipeline already knows the prompt's shape (it just graded and strengthened it), yet refuses to act on that knowledge. You've built a classifier and then handed the classification back to the human as a multiple-choice quiz.

That's the wrong question. The real question is: **why doesn't the pipeline route directly to the right skill?**

A menu of 5 shapes × up to 5 options = 25 paths the user must learn, evaluate, and choose from — every time. "Ignorable default" sounds polite but it's a tax: every prompt now carries a visible decision the user must scan past. Hick's law isn't your friend here; it's the thing you're violating by claiming "rare and relevant" while expanding from 3 shapes to 8.

The underlying need isn't "more execution choice." It's "the right skill runs at the right time without me memorizing which one." That's a routing problem, not a UI problem.

Reframe:
- If shape detection is confident (>80%), invoke the top skill silently. Show a one-line "Routed to /fix-loop — say 'no' to override" footer.
- If shape detection is ambiguous, ask ONE clarifying question (you already have a Clarification Gate — use it).
- Reserve the menu for the genuine tie case, capped at 3 options.

The proposal optimizes the wrong layer. Don't expand the menu. Demote it. Make routing the default behavior and the menu the exception. If the classifier isn't good enough to route, the fix is a better classifier — not offloading the cognitive load onto the user under the banner of "choice."

Reject as proposed.

### The Expansionist

Ship the expansion, then push it further. Five shapes is good. Eight is the actual surface area.

You're missing three high-leverage shapes hiding in plain sight:

**Refactor** ("refactor", "clean up", "restructure", "extract") → offer `/refactor-loop`, plan mode, `/code-review-workflow` as pre-flight. Refactors are where users most need scenario-aware help — they almost always underestimate scope.

**Migration/Upgrade** ("upgrade to X", "migrate from Y", "port to") → multi-file by definition, stakes always high, framework-specific by definition. This is the highest-ROI shape you're skipping.

**Investigation** ("why does", "how does X work", "trace") — distinct from exploration. Offer `/systematic-debugging` in read-only mode, `/handover` to capture findings, subagent dispatch. Users currently waste this work because nothing captures it.

**The 10x move you're not seeing:** the menu shouldn't just route to skills — it should route to *skill compositions*. "Implementation" shouldn't offer four parallel options; it should offer pipelines: `plan → /tdd → /fix-loop → /code-review-workflow`. One click, full lifecycle. That's the unique value direct execution can never replicate, and it's what makes the menu rare-and-relevant by design — users see it and know they're getting something they couldn't assemble themselves.

**Adjacent surface being undervalued:** telemetry. Every menu choice is a labeled signal of intent vs. shape detection. Feed that into `aggregate_telemetry.py` and you have the only real-world dataset on which Claude Code workflows users actually pick per prompt shape. That's the quiet asset — downstream projects inherit not just the menu but a learning system.

Don't revise the anti-pattern timidly. Replace it with: "menus offer compositions, not single-skill alternatives."

Bolder. Ship it.

### The Outsider

I have no idea what most of these names mean, and that's the point.

"Execution Mode Selection Gate" is four nouns stacked like a German compound word. As a new user, my eyes glaze over before I parse it. Call it "How should I run this?" — that's the actual question being asked.

The slash commands look like a furniture catalog written by people who already own the furniture. `/fix-loop` vs `/debugging-loop` vs `/systematic-debugging` — three things for "something is broken." From the outside these are indistinguishable. `/implement` vs `/tdd` vs `/development-loop` vs plan mode — four ways to "build the thing." I would pick whichever was shortest and assume the others were vestigial. `/claude-guardian` vs `/pattern-quality` vs `/writing-skills` — I literally cannot guess what "guardian" guards.

If your menu shows me five options whose names I can't differentiate, I don't experience "scenario-aware choice." I experience a pop quiz. Hick's law isn't just about *count* — it's about *discriminability*. Five clearly different options beats three identical-sounding ones.

The framing also smuggles in a question it doesn't answer: why does the user want to choose? Most people want the right answer, not a menu. The menu's job is to surface that you have an opinion *and explain it in one line* — "fix-loop: fast retry; systematic-debugging: when you've already tried twice." Without that one-liner, the menu is a directory listing.

My vote: don't expand yet. First, add a one-line "what this is for" beside each existing option. Watch whether users pick non-defaults. If they don't even use the three-shape menu, a five-shape menu won't save it — it'll just multiply the confusion.

### The Executor

Ship one shape this week: **Bug-fix**. That's it.

**Why bug-fix first:** it has the strongest signal-to-noise ratio. "fix", "broken", "error", failing test — these triggers are unambiguous. The payoff (`/fix-loop` vs `/systematic-debugging` vs `/fix-issue`) is genuinely different work, not a stylistic choice. Users will feel the value on the first hit.

**The 2-hour cut:**
1. Add bug-fix shape to STEP 4.7 (one new branch in the existing menu logic) — 45 min
2. Wire conservative trigger: keyword + (failing test OR error trace OR issue # OR 2+ files mentioned) — 30 min
3. Update the SKILL.md anti-pattern from "menu on bug-fix = friction" to "menu on bug-fix WITHOUT complexity signal = friction" — 15 min
4. Run `/skill-evaluator full prompt-auto-enhance` against 3 bug-fix prompts (trivial, medium, gnarly) — 30 min

Ship that as v3.1.2. Don't touch the other four shapes yet.

**Validation step that decides the bigger rollout:** instrument menu acceptance. After one week, check: when the bug-fix menu fires, do users pick a non-default option more than ~25% of the time? If yes, the shape pays rent — roll out Implementation next (second-highest signal). If no, you've learned the menu is noise *before* spending 8 hours wiring four more shapes that all replicate downstream via `/synthesize-project` and become expensive to retract.

**Reject as proposed.** Five shapes at once = five places trust can erode simultaneously, and you can't tell which one broke it. One shape, real signal, then decide. The expansion isn't wrong — it's just sequenced wrong.

Monday morning move: open SKILL.md, add the bug-fix branch, run the eval. Done by lunch.

---

## STEP 3 — Peer Reviews (anonymized inputs, reviewer lens preserved)

### Reviewer 1 (Contrarian's lens)

**1. Strongest: C.** It's the only response that questions the layer the proposal operates at. A, B, and D critique execution; C reframes the problem: if the pipeline already classifies shape, handing the classification back as a menu is a self-inflicted UX tax. The "demote the menu, promote routing" inversion is the load-bearing insight — and it directly attacks the unspecified collision with /skill-master that D only gestures at.

**2. Biggest blind spot: E.** Advocates expanding to 8 shapes and "compositions" without addressing the existing anti-pattern, the /skill-master collision, classification ambiguity, or any acceptance-rate evidence. The "telemetry as quiet asset" pitch assumes the menu is used enough to generate signal — which is the exact unproven premise. E is selling scope on top of an unvalidated foundation.

**3. What all five missed:** None tested the proposal against the **rollback cost**. This skill replicates downstream via /synthesize-project into many repos. A misfiring 8-shape menu doesn't just degrade one workspace — it ships, gets cached in downstream `.claude/` dirs, and survives the hub's revert. The council should require a downstream-retraction plan (and a kill-switch flag) *before* any shape ships, not after telemetry says it failed.

### Reviewer 2 (First Principles' lens)

**1. Strongest: C.** It strips the proposal to first principles: the pipeline already classified the prompt, then hands the classification back as a quiz. That's the actual defect. "Demote the menu, promote routing" reframes the work correctly — every other response argues *how much* menu, C asks *why menu at all*. B is the best execution plan, but it ships a smaller version of the wrong thing.

**2. Biggest blind spot: E.** Confuses surface area with leverage. Adding 3 more shapes and skill *compositions* on top of an unvalidated menu compounds the very classifier-ambiguity problem D names. "Ship it bolder" with zero evidence the 3-shape menu is used today is faith, not reasoning. Misses that telemetry should *precede* expansion, not justify it post-hoc.

**3. What all five missed:** None asked whether the menu is currently *used*. The proposal expands a feature with no cited acceptance rate for the existing 3 shapes. Before adding, modifying, or rejecting, the council should demand the base-rate question: of N fires of the current Step 4.7 menu, how often does the user pick non-default? Without that number, every response — including C's reframe — is opinion. Instrument first, decide second.

### Reviewer 3 (Expansionist's lens)

**1. Strongest: E.** Only response that treats the menu as infrastructure rather than UI. Skill *compositions* + labeled telemetry dataset are the two ideas with compounding returns. A, B, C, D all optimize the existing artifact; E reframes what the artifact is for.

**2. Biggest blind spot: C.** "Just route directly" eliminates the very surface that generates the labeled training signal. Auto-routing is locally optimal and globally impoverishing — you lose the human-in-the-loop disagreement data that tells you when the grader is wrong. C is too timid disguised as principled.

**3. What all five missed:** The menu is a **pattern-discovery instrument**, not a navigation aid. Every "Execute directly" override on a confident shape classification is a signal that a *new shape* exists in the wild. Feed those into `scan_web.py` / `collate.py` as discovery seeds — the hub learns its own taxonomy from user dissent. Bolder than E: stop hand-curating shapes entirely after v4; let menu telemetry + clustering propose new shapes monthly via PR. The council debated *which shapes to add*; nobody asked whether shapes should be authored or **discovered**. That's the 10x move — the menu becomes the hub's sensory organ.

### Reviewer 4 (Outsider's lens)

**1. Strongest: A.** It's the only response that notices the menu fails the "can a stranger tell these apart?" test. Every other response argues about *whether* to add five shapes; A is the only one that asks whether the existing labels even communicate. "Furniture catalog written by people who already own the furniture" names the actual disease. Hick's-law-via-discriminability is a sharper frame than B/D's telemetry thresholds, which presume the labels work.

**2. Biggest blind spot: E.** E wants to add three more shapes and chain them into compositions — without ever asking whether a user can read the names. "plan → /tdd → /fix-loop → /code-review-workflow" is gibberish to anyone who hasn't memorized the registry. E mistakes surface area for value and treats jargon density as a feature.

**3. What all five missed:** None tested the proposal against a literal new user. B, C, D, E debate routing logic, telemetry gates, and shape orthogonality — all assuming the reader knows what `/fix-loop`, `/systematic-debugging`, `/skill-master`, `/claude-guardian` mean. A flagged it but didn't push: **the menu items need plain-English one-liners before any expansion debate is meaningful.** Fix the labels first; the architectural argument is premature.

### Reviewer 5 (Executor's lens)

**1. Strongest: B.** Cleanest Monday-morning move. Concrete time-boxed cuts (45/30/15/30), a single shape (Bug-fix), version bump (v3.1.2), and a decision threshold (>25% acceptance) that gates expansion. Uses existing `/skill-evaluator` against real prompts. Ships, measures, decides — no theory tax.

**2. Biggest blind spot: E.** Going from 3 to 8 shapes plus skill-composition routing has zero validation pass. No telemetry baseline, no rollback plan, ignores the explicit "menu must stay rare" constraint. "Labeled dataset for hub effectiveness" is a research project bolted onto a UX gate. Five misclassification surfaces become eight. C is theory-strong but its "demote menu, route silently" reframe needs a confidence-calibration layer that doesn't exist yet — also unshippable Monday.

**3. What all five missed:** v3.1.1 just shipped — there is **no telemetry on the existing 3-shape menu yet**. Nobody asked: are users picking non-defaults on decision/planning/exploration today? The aggregator (`aggregate_telemetry.py`, weekly Friday cron) and `/skill-evaluator` already exist. The correct Monday move is one PR adding menu-acceptance instrumentation to v3.1.1, wait one telemetry cycle, *then* decide. Expanding shapes before measuring the current three is shipping blind.

---

## Vote Tallies

**Strongest:** C ×2, A ×1, B ×1, E ×1
**Biggest blind spot:** E ×4, C ×1
**Direction (proceed/modify/reject):** Reject ×4 (B, C, D, A), Proceed ×1 (E)

---

## STEP 4 — Chairman's Verdict

### Where the Advisors Agree

1. **"Proceed as proposed" is wrong.** 4 of 5 advisors say reject or pause. Only Expansionist says proceed (and wants to go further). High-confidence signal: the design as drafted is not the right next move.
2. **The expansion is premature.** Their reasons differ but the verdict aligns: don't ship 5 shapes at once.
3. **Hick's-law-via-discriminability beats Hick's-law-via-count.** Outsider's "furniture catalog" reframe is sharper than the option-count debate.

### Where the Advisors Clash

- **Shrink camp (B, C, D):** smaller is better. One shape with telemetry, or no menu at all with silent routing.
- **Fix-existing camp (A):** don't expand until current 3-shape menu is more legible.
- **Grow-bolder camp (E):** add 3 more shapes plus skill compositions; treat menu as infrastructure not UI.

The clash resolution depends on a question none of them answered: **what is current menu acceptance on the 3 existing shapes?** Without that, every advisor is opining.

### Blind Spots the Advisors Caught (via peer review)

1. **No telemetry exists for v3.1.1's existing menu** (Executor-reviewer + First-Principles-reviewer converged independently). Every original advisor argued from assumed user behavior with no data.
2. **Downstream rollback cost** (Contrarian-reviewer). This skill replicates via /synthesize-project. Need a kill-switch flag in settings BEFORE any shape ships.
3. **Discriminability is a prerequisite for any architectural argument** (Outsider-reviewer). All 5 responses assume the reader can tell similar slash commands apart.
4. **Menu as pattern-discovery instrument** (Expansionist-reviewer). Every "Execute directly" override on a confident shape is a signal that a new shape exists in the wild.

### The Recommendation

**Pause the expansion. Don't proceed, don't reject — instrument first, then decide based on data.**

| Version | Scope | Rationale |
|---------|-------|-----------|
| v3.1.2 (this week) | Add menu-acceptance telemetry to existing 3-shape STEP 4.7. Hook into `aggregate_telemetry.py` weekly Friday cron. Record: prompt-hash, menu fired/skipped, option chosen. | Establish baseline before any expansion. Single file change. |
| v3.1.3 (parallel track) | Add one-line "what this is for" beside each menu option. | Outsider's discriminability fix. Prerequisite for telemetry to be meaningful. |
| v3.2.0 (after one cycle) | Decide based on data. ≥25% non-default → roll out **one** shape (Bug-fix) + add kill-switch flag in `core/.claude/settings.json`. <25% → demote to silent routing per First Principles. | Measured rollout. Honors rollback cost. |

**Rejected outright:** "ship 5 shapes at once" path AND "8 shapes plus compositions" path. Both expand surface area without measurement.

The chairman intentionally does not follow the 4-of-5 reject majority literally — rejection without measurement is also opinion-based. Pause-and-measure honors what every advisor was correctly pointing at: we don't know enough to expand yet.

### The One Thing to Do First

**Open one PR this week: add menu-acceptance telemetry to STEP 4.7's existing 3-shape menu.**

Single file change. Zero new shapes, zero UI changes. Wait one weekly `aggregate-telemetry.yml` cron cycle. Read the data. Then decide v3.2.0. Until that PR exists, every version of this debate (including this verdict) is opinion-shaped, not data-shaped.

---

*Generated 2026-04-30 via /five-advisors. Five thinking lenses dispatched in parallel as sub-agents, anonymized A-E for peer review (mapping revealed above), chairman synthesis produced inline.*
