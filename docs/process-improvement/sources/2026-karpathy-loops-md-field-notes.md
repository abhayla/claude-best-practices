Source: uploaded image (88f7ebaa-1000479498.jpg) — shared by owner 2026-06-29
Original work: "loops.md, v060726" (working notes), reformatted as a conference-style paper
Author (as attributed in the document): Andrej Karpathy, Independent Researcher
Captured: 2026-06-29
Image: ./img/karpathy-loops-md-field-notes.jpg
Provenance caveat: attribution to Karpathy is as printed on the document; authenticity not independently verified. Capture the *ideas* regardless of byline.

# LOOPS.md: Field Notes on Agents That Run for Days
### A Short List of Rules for Letting the Model Drive

**Abstract.** Most agent systems die not from a weak model but from a weak harness. The model
can write code, review code, and verify its own output against a rubric it agreed to ten
minutes ago. What it *cannot* do on its own is decide **when to stop, when to restart, and
where to write the result** — that is the work of the loop. Treat the loop as a first-class
object: roles are separated, state lives on disk, contracts are negotiated between agents
before the first line of code, and the harness is read like a stack trace when something
breaks. Short loops, simple state, clean contracts. Everything else is decoration.

**Index terms.** agentic loops, Claude Code, harness design, generator-evaluator pattern,
sprint planning, file-system state, contract negotiation, trace reading, deletable scaffolding.

## I. Write the loop, not the prompt
A prompt is typed once and forgotten; a loop runs while you sleep. The unit of leverage stopped
being the prompt the moment models could follow a procedure unsupervised — what matters now is
the *procedure*. Iterating on a single message at 3 a.m. means you're still in the prompting era.
Close the tab, write the loop. The loop is short: **gather, reason, act, verify, repeat.**
Everything else is a footnote on those five verbs.

## II. Separate the roles
Three roles, three context windows, three system prompts:
- **Planner** — turns a vague human sentence into a sprint spec; never touches code.
- **Generator** — writes everything; forbidden from grading its own work.
- **Evaluator** — reads diffs, launches `playwright`, plays the app; told from message one that
  the code is broken and its job is to prove it.
Mixing roles is the most common failure: the model turns sycophantic the moment it grades itself,
and the loop quietly converges on slop.

## III. Negotiate the contract first
Before the generator writes a line, it proposes what "done" looks like and the evaluator pushes
back. They argue via markdown files on disk until they agree on a checklist of **testable
assertions**. ~27 criteria is reasonable for a small app; 10 is too few (the evaluator
rubber-stamps). The planner's spec is the boundary, but the **contract is what gets graded.**
This single change moved his runs from broken demos to working products.

## IV. Write to disk, not to context
Context windows lie — they compact, rot, and hide what you said an hour ago behind a summary you
didn't write. A file on disk does not. Keep `feature_list.json`, `progress.md`, `contract.md`,
and an append-only `log.md` with `## [YYYY-MM-DD] op | title` entries. The model should be able
to **crash, lose its session, and resume by reading three files.** If you can't describe your
state in three files, your state is too complicated.

## V. Let the loop restart
The best behavior in current frontier models is willingness to **throw everything away and start
over** when a run goes sideways. Older models patched until the codebase looked like archaeology;
newer ones, given a clean evaluator + a contract on disk, will delete the project at iteration 9
and ship a working version at iteration 11. Don't interrupt — the restart *is* the loop working.
Insert a human only when the **contract** is wrong, not when the build is.

## VI. Score the subjective
Taste is gradable if you write it down. Four weighted axes: **design, originality, craft,
functionality.** Calibrate on three reference sites the evaluator is told are good and three it's
told are slop. Output = a number 0–1 + a paragraph explaining the gap. The model won't *invent*
taste; it only converges toward the taste you described. The whole game is writing the rubric
carefully enough that converging toward it is what you actually wanted.

## VII. Read the traces
Every debugging insight about agent loops came from **reading the raw transcript**, not running
another experiment. Pipe the agent's output to a file, grep for the moment its judgment diverged
from yours, edit the prompt for that exact moment, run again. Same muscle as reading a stack
trace — except the trace is in English and most of it is the model talking to itself. Skip this
and you're tuning by vibe.

## VIII. Delete the harness
The harness exists to compensate for the model; as the model improves, half of what you wrote
last quarter becomes overhead. Context-resetting between sessions was load-bearing for one model
generation and dead weight for the next; sprint decomposition that kept a 4-hour build coherent
is now a constraint on a model that holds 2 hours in one head. **Re-read the harness against each
release and delete anything the model now does for free.** A harness that grows monotonically is
one you've stopped reading.

## IX. The bottleneck always moves
Coding solved → planning is the bottleneck. Planning solved → verification. Verification automated
→ taste. **You don't finish; you find the next thing to fix.** The point of the loop is to make
the next bottleneck visible. If everything feels smooth, you're not looking carefully enough.
Find the new bottleneck, fix it, ship a *smaller* harness, repeat.

---
*Footer:* © 2026 A. Karpathy. Personal use permitted. Independent reformatting of working notes
on long-running agent loops (loops.md, v060726). Freely available; ideas subject to revision.

---
## Relevance to THIS hub (why captured)
This is arguably the single most on-point external source for the hub's north star. Direct maps:
- **§I "write the loop"** → `/loop`, `/schedule`, `loop-engineering` workflow.
- **§II separate roles** → the hub's builder vs. independent verifier / `code-reviewer-agent` /
  `pre-git-merge-checker-agent`; "no self-grading" = `independent-test-verification.md`.
- **§III contract first** → autonomous-contract / `plan-before-coding.md`; "contract is what gets graded."
- **§IV write to disk** → `.claude/tasks/`, `.remember/`, session checkpoints, scratchpad rule, compaction-handoff.
- **§V let it restart** → trust-score "let the build fail/restart"; human only when the contract is wrong.
- **§VI score the subjective** → `config/trust-score.yml` weighted signals + rubric discipline.
- **§VII read the traces** → `prompts.md` logging; grep-the-divergence debugging.
- **§VIII delete the harness** → `rule-curation.md` (reactive, prune what the model does for free) +
  the CC-adoption "delete hand-rolled once platform does it" doctrine (`cc-adoption-scout`).
- **§IX bottleneck moves** → the goal-pulse / continuous-improvement cadence.
Use this as a yardstick when we run the process-improvement pass: where does the hub still
self-grade, grow its harness monotonically, or keep state in context instead of on disk?
