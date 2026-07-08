Source: https://x.com/alex_prompter/status/2074198124898181121
Captured: 2026-07-08
Author: Alex Prompter (@alex_prompter)
Posted: 2026-07-06
Engagement (at capture): 2569 likes, 251 RTs, 111 replies, ~716k views

# "You have a few days to clone Fable 5 into Opus 4.8"

> ⚠️ **Unverified model/marketing claims — do NOT propagate:** "July 12 is the last
> day Fable 5 sits in your plan for free, then pay-per-use credits"; Fable ≈ `$10/M in,
> $50/M out` (~2× Opus 4.8); Sonnet 5 intro ≈ `$2/$10` per M until end of August. These
> are the author's assertions; verify against the `claude-api` skill / official docs
> before treating any as fact. This post is also **promotional** — it ends with a
> linktr.ee pitch for the author's paid "Claude skills bundle."

## Relevance to this hub — MODERATE (validates existing philosophy; little new technique)

The article's core thesis is genuinely aligned with the hub, but it does not add a
mechanism the hub lacks — it's a consumer-facing framing of what the hub already does.

**The thesis (worth keeping):** *"The model was never the asset. The way it thinks is —
and a way of thinking can be written down, pulled out, and run on a cheaper model."*
Attaching a workflow to one model is "building on rented land"; what survives every
deprecation is the describable reasoning system (skills, system prompts, rules).

**How it maps onto the hub (all already covered):**
- **Portable reasoning > model weights** → the hub's entire premise (patterns/skills/rules
  are model-agnostic, distributable) + **G4** (stay a thin layer on the platform).
- **"Asset vs throughput" spend rule** — *"anything you'll still use in a month (system
  prompt, skill, big decision) is an asset — pay the frontier model once to produce it;
  anything you throw away by Friday is throughput — run it cheap"* → this IS `model-routing.md`
  (cheapest-sufficient per dispatch; inherit the frontier model only for durable/high-stakes
  judgment). Nice external restatement of the routing rule's economic rationale.
- **STEP 3 "prove the transplant took" via a trap test** (feed a rigged "$4.0M→$4.2M is a
  5% gain, not 20%" question; a manual-loaded model must re-derive and refuse the wrong
  number) → maps onto `independent-test-verification.md` / adversarial verification. The
  specific "verify with a deliberately-wrong input" trap is a tidy, reusable eval idea.
- **"Extract procedures, not a summary"** (*"'check your work' is a vibe; 'for any
  percentage find both endpoints yourself and divide, because that's where flipped signs
  hide' is a procedure a model can run"*) → restates the hub's **laws-not-tips** principle
  (also the sharpest point in the [Avid note](2026-07-06-avid-agentic-os-fable5-8-builds.md))
  and the writing-skills "make it executable" standard.

**What it does NOT add:** no new architecture, ledger, loop, or gate — it's a single
extract→load→trap-test technique plus a spend framing, both already embodied in hub rules.

## One reusable idea worth the improvement pass

- **"Trap-test" verification recipe** — verifying a transplanted/updated skill or system
  prompt by feeding a *deliberately-wrong* input whose error is subtle-but-checkable, and
  asserting the model catches and refuses it (not just that it "sounds right"). Consider
  noting this as a concrete eval technique in the skill-evaluator / `independent-test-verification`
  flow — a cheap, high-signal regression check for reasoning skills. (Low priority; largely
  a naming/example add over existing adversarial-verification doctrine.)

## Full article text (verbatim, as extracted)

July 12 is the last day Fable 5 sits inside your plan for free. After that date it moves to pay-per-use credits, and most people are about to spend the week arguing over whether it's worth keeping. That argument misses the whole point. The model was never the thing worth keeping. The way it thinks is. And a way of thinking can be written down, pulled out, and run on a cheaper model that isn't going anywhere. I'm going to show you how to extract Fable 5's entire operating manual while access is still free, load that manual into Opus 4.8, and prove the transplant actually took. Ten minutes today, and you own the reasoning instead of renting the model.

**The model was never the asset.** Every model gets deprecated, repriced, or replaced eventually — the one guarantee in this field. Attaching your workflow to a specific model is building on rented land. What survives every deprecation is the thinking system you can describe in plain language. Fable 5's edge over a cheaper model isn't locked inside weights you can't touch: it's a way of reading what a request is actually asking for, breaking a hard problem into checkable pieces, verifying its own work instead of trusting what sounds right, and refusing to guess when it doesn't know. All of that is describable — which makes all of it portable. Get Fable to write that description down and you can hand it to Opus 4.8 today, Sonnet 5 tomorrow, and whatever ships next quarter.

**STEP ONE: extract the manual, not a summary.** Most people get a mediocre result because they ask for the wrong thing — they ask Fable to "explain how you think" and get a page of pleasant generalities. You don't want a description of the thinking; you want the procedures, written so a sharper-but-lesser model can execute them without you in the room. The difference is specificity. "Check your work" is a vibe. "For any percentage, find both endpoints yourself and divide, because that's where flipped signs hide" is a procedure a model can actually run. Paste the extraction prompt into Fable while your plan access is still live; if it stops mid-document, reply "continue"; if a section feels thin, tell it to expand that section only. What comes back is a portable reasoning engine, written in your model's own voice, at the peak of its capability. Save it — that file is the whole point.

**STEP TWO: transplant it into Opus 4.8.** The manual has to become the layer Opus 4.8 runs on top of. Fast way (app): open a Project in Claude, paste the extracted manual into the Project instructions, set the model to Opus 4.8 — every conversation now inherits Fable's operating manual before it reads your task. Durable way (API): a script that calls Fable once, saves the manual to a file, and loads that file as Opus 4.8's system prompt on every future call. Same manual, on a model ~half the cost that isn't being repriced tomorrow.

**STEP THREE: prove the transplant took.** Loading a manual isn't the same as the model using it. Test it with a trap: give plain Opus 4.8 and manual-loaded Opus 4.8 the same rigged question. Try "$4.0M to $4.2M is a 5% gain, not 20%." Plain Opus often waves it through because the sentence reads smoothly; Opus running Fable's manual should stop, re-derive the percentage, catch the wrong number, and refuse to ship it. If it catches the error, the transplant took. If not, your manual was too vague on verification — go back and make the verification part procedural.

**The money.** Fable ≈ $10/M input, $50/M output (~2× Opus 4.8); Sonnet 5 intro ≈ $2/$10 per M until end of August; a full extraction run today inside your plan costs nothing, after the switch it's a few dollars of credits. Anything you'll still use in a month (a system prompt, a skill, a big irreversible decision) is an asset — pay Fable once to produce it. Anything you'll throw away by Friday (drafts, chat, quick summaries) is throughput — run it on Opus or Sonnet. Extraction is the purest asset play: one Fable session today, output that keeps paying back on every cheaper call.

**BONUS:** turn repeat work into skills while you're in here — for each weekly workflow, paste a skill-extraction prompt into Fable, answer its questions honestly, and get back a skill file that runs on any model forever at no ongoing cost.

**What you walk away with.** Most will read the switch as a loss; operators read it as a harvest — ten minutes turning a temporary model into a permanent asset, then running Fable-grade reasoning on a model that costs half as much. "The panic is optional. The manual is forever. LLMs don't think, you do."

*(Article closes with "THE SCRIPT" — `fable_to_opus.py`, referenced but not included in the extracted text — and a linktr.ee/alex_prompter promo for a paid Claude skills bundle.)*
