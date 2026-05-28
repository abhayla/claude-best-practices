---
name: zoom-out
description: >
  Generate a one-layer-up map of the surrounding modules, their callers, and
  how the current code fits into the bigger picture. Use when the user is
  unfamiliar with a section of code, says "zoom out", "give me the bigger
  picture", "how does this fit", or needs altitude before diving deeper.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "[file path or area to zoom out from]"
version: "1.0.0"
---

# Zoom Out

The agent has been working close to the code and now needs altitude. Stop, go up exactly one layer of abstraction, and produce a **map** of the surrounding modules and callers — not an essay.

**Focus area:** $ARGUMENTS

---

## Process

1. **Anchor.** Identify the file, module, or directory the user is currently working in (from `$ARGUMENTS` or the most recent context). If ambiguous, name the candidates and ask one consolidated question.
2. **Walk outward one level.** Find who calls into the anchor, what it calls into, and what siblings exist in the same package or directory. Use `Grep` for callers and `Glob` for siblings — do not crawl the entire repo.
3. **Read entry points.** Read (don't grep blindly) the immediate callers — enough to *name* what they do, not enough to understand every detail. One sentence per caller is the right level of zoom.
4. **Use the project's words.** Where a `CONTEXT.md` / `CONTEXT-MAP.md` exists (see `/grill-with-docs`), use that vocabulary. Where it doesn't, use the names the code itself uses — never invent labels like "service layer" or "data layer" if the codebase doesn't.
5. **Render the map.** Produce the output shape below. Then ask: *"Where would you like to focus next?"*

---

## Output Shape

A short map, not a tour. Five sections, each tight:

- **Where we are** — one sentence naming the current module in domain terms.
- **Who calls it** — bullet list of upstream callers with one-line descriptions.
- **What it calls** — bullet list of downstream collaborators with one-line descriptions.
- **Sibling modules** — bullets, only the ones that share responsibility. Omit the section entirely if there are no meaningful siblings.
- **The bigger picture** — one or two sentences placing this module in the flow.

Each bullet is a name + a one-line description. If a description needs more than one line, the bullet is at the wrong altitude — go up another half-step or push detail into a follow-up.

---

## When to Climb Further

This skill is deliberately a single layer. If the user, after seeing the map, still needs more altitude:

- **Run it again** with a parent module as the new anchor — composes naturally
- **Switch to `/improve-codebase-architecture`** if the user is hunting for refactor opportunities, not just orientation
- **Switch to `/strategic-architect`** if the user wants project-level health, not module-level mapping

---

## Example

Anchor: `src/orders/repository.py` in a hypothetical project with a `CONTEXT.md` defining "Order" and "Fulfillment".

A good zoom-out reads roughly like this — Order intake module persists Orders and exposes a read view, called by the API handler in `routes.py` and by the background dispatcher; it calls into the database adapter and the event bus; siblings include `validator.py` and `pricing.py` which share the same Order domain; the bigger picture is that Orders flow from intake into Fulfillment via the dispatcher.

A bad zoom-out reads like a tour: paragraph after paragraph of "this then this then this", method-by-method tracing, every function listed. If the map cannot be skimmed in 30 seconds, it failed.

---

## CRITICAL RULES

- MUST use the project's domain vocabulary if `CONTEXT.md` exists — never substitute generic labels
- MUST NOT produce a wall of text — this is a map, not a tour
- MUST NOT invent layer names ("service layer", "infra layer") that the codebase does not itself use
- MUST stop at one layer of abstraction up — do not climb the whole stack in one shot
- MUST NOT recommend a refactor — that is `/improve-codebase-architecture`'s job
- MUST NOT crawl the entire repo — bounded `Grep`/`Glob` only, scoped to the anchor's immediate neighbourhood
