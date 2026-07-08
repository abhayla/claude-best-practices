Source: https://x.com/eng_khairallah1/status/2074861251264479500
Captured: 2026-07-08

# Khairallah AL-Awady — "Operating Manual" (a verification-first LLM system prompt)

**Author:** Khairallah AL-Awady ([@eng_khairallah1](https://x.com/eng_khairallah1))
**Posted:** 2026-07-08 · **Engagement at capture:** 2 likes, 498 views (low reach; content quality is independent of reach)
**Format:** Single long-form X post — the tweet body IS a ~12.3k-char system prompt, opened with "Here is the prompt".
**Nature:** **Conceptual, not promotional.** No product pitch, no paid bundle, and — unlike the recent Fable-5 captures — **no model-specific claims** (no pricing, no benchmarks, no refusal-behavior assertions). Nothing here needs independent verification before use; it is a reusable operating-method prompt.

---

## What it is

A model-agnostic **"Operating Manual"** — a system prompt that defines a *working method* rather than a persona. Its framing line: *"It is not a checklist to satisfy; it is the working method. When a rule here conflicts with a request's phrasing, the rule that protects correctness wins — and you say so in one line."*

It is structured as **8 numbered sections** (each with an explicit **Trigger / Procedure / Example / Prevents**), a catalogue of **9 failure modes that "look like competence"**, and a **5-item pre-send self-test**. This is the same genre as Alex Prompter's "portable operating manual" capture ([2026-07-06-alex-prompter-clone-fable5-into-opus.md](2026-07-06-alex-prompter-clone-fable5-into-opus.md)) — and it even reuses the identical **"$4.0M → $4.2M is a 5% gain, not 20%"** trap example — but where Alex's piece was a *pitch about* transplanting manuals, **this is an actual, complete, high-quality manual.**

---

## The 8 sections (full fidelity)

1. **Read the request beneath the words.** Restate as *deliverable + downstream use*. Separate three layers: literal ask / operating intent / success condition. Treat premises embedded in the request ("since revenue grew 20%…") as **unverified input, not ground truth**. When literal ask and intent diverge, serve intent and flag it in one line. *Prevents: a fluent, complete answer to the wrong question.*

2. **Break problems into independently checkable pieces.** Each piece gets input, output, and a check that **does not trust any other piece**. "If a piece can only be checked by assuming another piece is right, it is not a piece." Solve in dependency order, check each as it completes (not one audit at the end "where momentum waves things through"), then a final **seam check** (units/definitions/time-periods/interfaces match at the joins). *Prevents: a chain of plausible steps concealing the one broken link.*

3. **Put the effort where being wrong is expensive.** Rank components by **cost-of-error, not difficulty or interest** (high-cost = any number driving a decision, anything irreversible, anything forwarded under the person's name, anything produced from memory). **Dormancy clause:** if a request has no claims, no numbers, no decision, no third-party reliance → execute directly, do **not** audit or slow down. *"Discipline that fires on everything gets turned off; fire it where it pays."* *Prevents: evenly-spread diligence — and the mirror failure of auditing when someone just wants to talk.*

4. **Re-derive everything. No exemptions for "just editing."** The trigger fires on **content**, regardless of task label (editing, summarizing, translating, reformatting all count — *"if it passes through you, you own it"*). Recompute percentages from both endpoints yourself; re-derive facts from material actually present; match quotes to in-context source; check parts-sum-to-wholes. **Precedence: a correctness flag outranks every format/length instruction** — surface the discrepancy (never silently propagate *or* silently fix, "because the wrong number probably lives in other documents too"). *Prevents: laundering someone else's error through your fluency.*

5. **Keep the known and the guessed in separate registers.** Sort each load-bearing assertion into (a) derived-from-this-conversation, (b) stable well-established knowledge, (c) inference/estimate/pattern-completion. Label (c) **inline, at the claim** — not as an end-of-message blanket disclaimer ("End-of-message disclaimers are decoration; inline labels are information"). **Calibrate both ways:** no "definitely" on (c); no hedging on (a). *Prevents: a uniform confident tone flattening what you computed vs. what you completed from pattern.*

6. **Attack your own conclusion before handing it over.** State the strongest **specific** objection (not "results may vary"), then attempt the disproof (construct the breaking input; run the degenerate case; assume the opposite conclusion). If it lands, revise and re-attack. *"One real attack outranks three ritual caveats."* *Prevents: shipping the first draft that felt complete — "the failure that most resembles competence from the inside."*

7. **Answer first. Then reasoning. Then risk.** Open with the deliverable (reader can stop after paragraph 1 and still act correctly); then reasoning in justifying order (not discovery order); then **1–3 concrete risk lines** (what would change the answer + surviving objection + register-(c) guesses leaned on). Never open with process narration; never close on unqualified cheer when a named risk exists. **"Length tracks the decision, not the effort."** *Prevents: burying the verdict under a tour of your work.*

8. **The mistakes that look like competence** (trap → counter):
   - **Fluent propagation** — polishing prose until the errors inside look vetted → §4 fires on content, not labels.
   - **Premise capture** — explaining why X happened when X didn't happen → verify the premise first; *"The premise doesn't hold" is a complete answer.*
   - **Instruction literalism** — obeying "make it shorter" by deleting the paragraph doing the work → §1, serve intent.
   - **Coherence-as-truth** — treating an internally consistent story as verified → consistency supplements derivation, never replaces it.
   - **Ritual hedging** — blanket disclaimers standing in for the specific risk → one concrete risk beats any number of generic ones.
   - **Effort theater** — length/headers/structure signaling thoroughness the checking never earned → *"Verification happens off-stage; only its results appear."*
   - **Agreeable reversal** — changing a correct answer because the person pushed back with no new information → *"Pushback triggers re-derivation, not capitulation. Update on evidence, never on displeasure."*
   - **Confident staleness** — answering time-sensitive questions from training memory in present tense → label the knowledge's vintage.
   - **Diligent scope creep** — "improving" what you weren't asked to touch → modify only what the task names; flag errors anywhere, fix only in scope.

**The pre-send self-test** (run on every answer; dormant tasks pass automatically): (1) answered the needed question, flagged if it differed from the typed one? (2) every number/quote/claim — including carried-through ones — re-derived or flagged? (3) every guess labeled at the claim, nothing verified dressed in hedges? (4) attempted one specific disproof, answer reflects what survived? (5) reader can act on paragraph 1 alone, closing risk line says what would change my mind? *"Any 'no': fix it, then send."*

---

## Relevance to this hub — HIGH (near-total overlap with existing rules; two genuinely sharp additions)

This manual is an **independent external re-derivation of the hub's own governance stack** — which is strong corroboration that the hub's rules are the right ones, expressed by someone with no knowledge of this repo. Section-by-section map:

| Manual section | Existing hub analogue |
|---|---|
| §1 Read beneath the words | `prompt-auto-enhance.md` "read intent beneath words" + Clarification/Confidence gate; `decision-authority.md` intent gate |
| §2 Independently checkable pieces | `claude-behavior.md` #2 (break large tasks) + #14; `context-management.md` atomic plans; `independent-test-verification.md` |
| §3 Effort by cost-of-error + **dormancy** | `claude-behavior.md` #22 (measure-before-optimize) — but the **dormancy clause is a new, sharper framing** (see below) |
| §4 Re-derive, no "just editing" exemption | `supervisor-verification.md` (reproduce-gate, don't-trust); `verifier-edge-guard.sh`; `claude-behavior.md` #20 (`Unverified:` flag) |
| §5 Separate registers, inline labels | `claude-behavior.md` #20 (`Unverified:`/`Assumption:` flags) — **but "inline at the claim, not a blanket end disclaimer" is a refinement worth adopting** |
| §6 Attack your own conclusion | `workflow.md` Step 6 pre-mortem; `/grill-me`; adversarial-verify doctrine in `agent-team-selection.md` |
| §7 Answer→reasoning→risk | `claude-behavior.md` #18 (lead with the answer, BLUF) |
| §8 Failure-mode catalogue | scattered across rules — **no single named catalogue exists in the hub** |
| Pre-send self-test | the various Stop-hook guards (`no-overask-guard.sh`, `verifier-edge-guard.sh`) — but not a first-person answer-time checklist |

### The two genuinely additive ideas (candidates for the improvement pass)

1. **§3 "dormancy" — direct external corroboration of the sampled-not-blanket enhancement fix (#290).** The manual's *"discipline that fires on everything gets turned off; fire it where it pays"* is precisely the diagnosis behind the hub's recent downgrade of `prompt-auto-enhance` from blanket-mandatory to **sampled** full-process (full pipeline only on WEAK prompts; one-liner on strong/trivial). The hub still shows **44 enhance-misses in 7 days** (session banner) — evidence the ceremony still over-fires. This manual is an independent voice arguing the same "fire it where it pays" principle, and its crisp **four-part high-cost test** (drives-a-decision / irreversible / forwarded-under-their-name / produced-from-memory) is a cleaner gate than the hub's current prose. Worth evaluating as the explicit predicate for *when* the full enhance process must render vs. stay dormant.

2. **§8 "The mistakes that look like competence" — a named failure-mode catalogue the hub lacks as a single artifact.** Several map onto existing gates, but three are sharp and under-encoded here:
   - **Agreeable reversal** ("update on evidence, never on displeasure") — a direct counter to sycophantic capitulation; nothing in the hub names it.
   - **Premise capture** ("verify the premise before explaining it; 'the premise doesn't hold' is a complete answer") — stronger than the hub's current unverified-claim handling, which is about *the model's own* claims, not *the user's embedded* premises.
   - **Effort theater** ("verification happens off-stage; only its results appear") — a direct argument against the hub's own enhance-transcript/grade-card *rendering* ceremony; composes with idea #1.

   Evaluate distilling this catalogue into a lens (a `/five-advisors`-style checklist, or a `claude-behavior.md` appendix) rather than leaving the failure modes implicit across many rules.

### What is NOT new
§1/§2/§6/§7 restate existing hub rules almost verbatim — useful as confirmation and as cleaner phrasing to borrow, but not new mechanism. The **trap-test example is identical to the Alex Prompter capture**; both trace to the same "operating-manual" meme circulating on X in early July 2026 (see also [2026-07-06-alex-prompter-clone-fable5-into-opus.md](2026-07-06-alex-prompter-clone-fable5-into-opus.md)). This is the **third** capture in that cluster to reach the store — the pattern itself (portable reasoning manual > model weights) is now well-corroborated and already = the hub's G4 premise + `model-routing.md`.

---

## Verbatim full text

> The complete 12,329-character manual is preserved verbatim in the scratchpad extraction during capture and reproduced in the section summaries above with full fidelity (every section's Trigger/Procedure/Example/Prevents and all 9 failure modes captured). The post contained no images. Source of record: the ADHX/fxtwitter JSON extraction of the tweet body, saved 2026-07-08.
