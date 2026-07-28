---
name: whatsapp-flow-map
description: >
  Use when building or updating a WhatsApp conversation-flow map — a card-by-card HTML
  artifact of message templates, chatbot flows, keyword routes, and journey nudges (e.g. the
  PIFS "conversation, card by card" SSOT) — or when asked for a "WhatsApp flow map",
  "conversation map", "chat flow diagram", "response-flow map", or to check that every
  button/quick-reply/keyword is wired to its next message. Renders every card as a mini
  WhatsApp phone screen, animates the connections, makes every tap navigate to the connected
  reply (scroll-to-center + highlight, like receiving the message), and AUDITS wiring:
  a button with no route is a defect to surface, never to invent around.
type: workflow
allowed-tools: "Skill Read Write Edit Bash Artifact"
version: "1.0.0"
triggers:
  - whatsapp flow map
  - conversation map
  - chat flow diagram
  - whatsapp response flows
  - card by card map
  - button wiring audit
---

# WhatsApp flow map

Specialized sibling of `modern-data-pipeline-diagram` (same repo, same engine lineage) for ONE
subject: **WhatsApp conversation estates** — templates, chatbot flows, keyword routes,
guardrails, journeys. Produce ONE self-contained HTML file (inline CSS+JS, no external
fetches — Artifact CSP) and publish with the `Artifact` tool. First load `artifact-design`
for visual calibration; this skill owns the flow-map mechanics.

## When to use / not use
- USE: creating or updating a WhatsApp conversation map ("card by card", "flow map",
  "response flows"), auditing button/keyword wiring, or presenting a Wati/Meta template
  estate visually.
- NOT: generic data-architecture diagrams → `modern-data-pipeline-diagram`; quantitative
  charts → `dataviz`; editing the live Wati dashboard → `wati-dashboard-automation`.

## The three load-bearing ideas

### 1. Every card is a mini WhatsApp phone screen
Do NOT hand-author phone chrome per card. Cards are plain `.node` divs (eyebrow `.eye`,
bubble `.bub` with `.btxt`/`.meta`/`.qr` buttons, `.subnote`); a JS **phone-stamper** wraps
each bubble at load into a phone frame derived from the node's own classes:
- default (business sends) → dark-green WhatsApp header: avatar + business name + "online",
  wallpaper body, white incoming bubble;
- `.out` (customer types/taps) → "You" header, green outgoing bubble, right-aligned;
- `.int` (internal/staff) → "Staff phone" header, violet tint;
- `.kw` (dashboard captures / chatbot kits) → phone frame with a "Wati flow" header;
- `.ext` (external links / non-WhatsApp surfaces) → NO phone frame; dashed card.
Identity travels with the card (dragged cards still read as what they are) because the
chrome is stamped from the DOM, never hand-duplicated.

### 2. Tapping a button takes you to the reply — like receiving it
The edge registry (`data-edges="btnId>targetId:kind, …"` on each stage's
`<svg class="wires">`) does double duty:
- the wiring engine draws animated connectors (marching-ants + travelling packet), AND
- the **nav layer** makes every `from` element clickable: click → resolve target's `.node` →
  `scrollIntoView({block:'center'})` → a WhatsApp-style receive animation (pop + green ring
  pulse) on the target. Multi-target froms highlight all, scroll to the first. A drag that
  moved >4px suppresses the click (drag and tap coexist).
Applies to EVERY navigable element: quick-reply buttons, URL buttons, list rows, typed
keyword cards (`.out` nodes with an id in the registry are tapped as a whole card).

### 3. Wiring is AUDITED, never assumed — and gaps are asked, not invented
The **validation layer** runs at load and the AUTHOR runs the same audit at build time:
- every `.qr .b` must have an id AND at least one outgoing edge; violations get an
  `UNWIRED` badge on the button + entry in a sticky audit pill (bottom-right: red
  "⚠ N unwired taps" cycling through them, green "all taps wired ✓" when clean);
- edges referencing missing ids are listed (broken wire = defect);
- the map's own standing rules resolve the CLEAR cases (e.g. a universal "Know More" →
  the KM menu route; "Talk to advisor" → the advisor handoff; "Call me" → the callback
  flow). Wire those as `design` edges citing the rule.
- **Label precedent IS a clear instruction (owner ruling 2026-07-28):** a button whose
  label matches or nearly matches an already-wired button follows that precedent —
  same label → same target ("Share" follows the wired "Share on WhatsApp"; "Open
  account" follows the wired "Open demat account"). Wire it (`design` if the route
  isn't live yet); do NOT park it as an owner question. When two precedents conflict,
  decide by the audience/context the map records and log the reasoning in the
  changelog/commit — never as text under the card (see "Cards carry NO commentary").
- **Only a label with NO wired precedent and no standing rule is left visibly UNWIRED
  and turned into an owner question. NEVER silently invent a route or a reply card.** A proposed new card, if the
  owner asks for one, is tagged `DRAFT — needs owner review` (nothing goes to Meta/Wati
  from an unrecorded draft).

Build-time audit (adapt paths):
```python
# extract data-edges pairs + all id= attributes + .qr .b buttons; report:
#  (a) edges whose from/to id doesn't exist, (b) buttons with no id or no outgoing edge,
#  (c) orphan cards (never source, never target) — orphans are FYI, not defects
#  (terminal confirmations and info cards are legitimately unwired).
```

### 4. The map is a working surface: fold, filter, versions, live variables (owner rules 2026-07-28)
- **Foldable annotations:** big non-card panels (approval gates, changelogs) are `<details class="gates"><summary>…</summary>…</details>` — collapsed by default so cards get the space; the reader chooses to see them.
- **State filter bar:** a sticky chip row (`#wffilter`, engine module) filters cards by state,
  derived from each card's `.bstat` tag (live / build / design→pending / review / retire; no
  tag → info). Multi-select; **retired is OFF by default** — retired cards are hidden, not
  deleted. Toggling refires `wireAll()`; the engine skips edges with a hidden endpoint.
- **Version model — max TWO versions per message:** a true rewrite (v1→v2, interim→new) is
  ONE message with two cards tagged `data-ver="current"` / `data-ver="previous"`. The version
  switch shows one set at a time (Current default; deleted messages live on as `previous`).
  Anything older than the previous version is removed from the map. Never stack several
  versions' copy inside one card.
- **One card = one message, strictly:** sequential sends (Day-3 / Day-7 / Day-14 nudges) are
  DIFFERENT messages, not versions — split packed cards into one card per message, each with
  its own buttons and wires.
- **Cards carry NO commentary (owner ruling 2026-07-29, option b):** no subnotes, no
  fixnotes, no version sagas, no forensic timestamps under or inside cards — a card is the
  message, its header identity (template name · category chip · state tag · date chip), and
  its buttons, nothing else. History lives in the artifact's version archive; functional
  rules live in the design SSOT doc; unresolved issues surface through the audit pills;
  never-shipped failed candidates (a v6 that Meta flipped and was never wired) are deleted,
  not stacked. A struck-through "deleted from live" remnant inside a body is previous-copy
  debris — remove it.
- **Named live variables, never positional, never hardcoded samples:** bodies carry
  `<span class="wfvar" data-var="client_id"></span>` chips using the REAL parameter names
  ({{name}}/{{client_id}}-style, per the Wati paramName rule) — never `{{1}}`, never a baked-in
  "Rahul". One shared sticky **Sample values** bar (`input[data-var-input=…]`, pre-filled with
  the canonical sample identities) live-fills every chip on the page simultaneously — exactly
  like Wati's template-creator preview — so a tester can type one value and verify it flows
  consistently across ALL messages. Empty field → the chip shows its `{{var_name}}`.

### 5. The map is a test bench: manifest, lint, search, links, lenses, simulator (owner-approved 2026-07-29)
- **Machine-readable manifest (build FIRST — highest bug-prevention value):** the build step
  GENERATES `<script type="application/json" id="wfmanifest">` from the cards (never
  hand-maintained): per card — id, template name, state, category, version, buttons
  (label→targets), last-updated. Any session can then diff map-vs-live-Wati mechanically,
  turning the "map vs Meta drift is a bug" law into an automated check.
- **Invariant lint pill** (`#wflint`, bottom-left twin of the wiring pill): checks
  current-version, non-retired, customer-facing cards for — bare endings (no next-action
  buttons; explicit `data-terminal` exempts), >3 buttons, staff names, reward-amount/credited
  claims, referral terms without the disclosure link, button labels >20 chars, missing HI
  twin (grey, HI mode only). Red = compliance, amber = craft, grey = coverage. Exemptions
  live visibly in the HTML, never inside the checker. The same button rules are ALSO
  enforced at authoring time by `wati-template-create-and-track` (pre-submit validation);
  the rule text lives once, in the Meta categorization policy doc §4b — both skills reference it.
- **Search** (`#wfsearch` in the filter bar): ≥2 chars matches bodies, template names,
  ids, button labels among VISIBLE cards; first hit centers + pulses; Enter steps; Esc clears.
- **Deep links:** `#card-id` in the URL centers + pulses that card on load, auto-enabling
  whatever filter hides it. Every phone header carries a 🔗 copy-link (canonical artifact
  URL from `data-canonical` on `#wffilter` — NEVER the iframe src, which holds a token).
  Verify hash survival in the artifact viewer per deployment; search box is the fallback.
- **Category-cost lens** (`#wflens`): retints cards by Meta cost class (MKT red · UTILITY
  green · session/flow blue · internal violet) + a visible count line — answers "how much
  of the estate is exposed to the marketing cap" at a glance.
- **Last-updated chips:** build extracts the latest date per card into `data-upd`; shown
  as a chip; a "recent 7d" filter chip isolates fresh changes. Cards without a date are
  unaffected (coverage fills incrementally).
- **EN/HI toggle** (frame-first): HI mode swaps to `[data-lang="hi"]` bodies where recorded;
  a card without one shows a marked "HI twin not recorded on the map" placeholder (counted
  grey by lint) — missing twins become visible, never invisible, and are ported
  incrementally from the sign-off pack, never invented.
- **Conversation simulator:** ▶ on entry-point cards (`data-entry`: outbound templates +
  typed-keyword cards) opens a fixed phone pane that plays the flow as a real thread —
  taps append the wired reply, multi-target taps offer a chooser, unwired taps show an
  honest dead-end, breadcrumb + undo/restart, sample values applied. Plays ONLY what is
  wired; never invents a reply; sends nothing.
- **Free-text composer + LIVE-VERIFIED routing (owner-approved 2026-07-29):** the pane has
  a type-a-message composer (+ a "▶ new chat" chip for a blank session). Typed text routes
  through `<script type="application/json" id="wfroutes">` — the keyword registry **pulled
  from the live tenant** (per-rule GET on the automation-rules API + getDefaultReply),
  never assumed: each entry = literal keyword, exact/contains, on/off, target card;
  `dflt` = the verified welcome/fallback/off-hours/slow-reply behavior. Routing order:
  (1) an OPEN question/collector card (`data-question`) consumes input first — keyword
  routing SUSPENDED, exactly like the live trap class; (2) exact rules, then contains
  (literal, case-sensitive as the live rules enumerate case variants); a rule that matches
  but is DISABLED live says so and falls to default; (3) default: first message in a new
  chat → the welcome flow; else the verified no-match truth (e.g. fallback OFF → "no bot
  reply; R2 after N min in-hours; R1 off-hours") + an optional **design-intent hint**
  (from the map's typed-intent cards) ALWAYS labeled "NOT live behavior". Registry
  verification is part of the build: pull the rules live, reconcile drift onto the map
  (§6c: a stale rules card, a disabled rule behind live-wired buttons, a changed default
  are DEFECTS to record), stamp `verified` with the date. Known unknown to re-verify per
  tenant: whether a keyword rule beats the welcome flow when both match a first message
  (this build assumes keyword-first).

## Conversation-UX quality bar (check every card you author or edit)
These mirror the estate's standing invariants — a card violating them is a defect:
- every in-session bot reply ENDS with ≤3 context-relevant next-action buttons (>3 options
  → a list message, 10-row cap); no bot message ends bare;
- no personal staff names in customer-facing copy — role words only ("our representative");
- no reward amounts or credited-confirmations — fixed program terms + Console pointer only;
- referral content carries the disclosure link; risk line where the estate requires it;
- opt-out (STOP / बंद करो) always routes to the opt-out terminal, and no flow continues past it;
- EN + HI twins exist for every user-facing message (or the card notes the HI twin's status);
- category chips (MKT/UTILITY/FLOW/KEYWORD/INTERNAL) and state tags (live/build/pending/
  review/retire) on every card — the map is a status ledger, not just a picture.

## Non-negotiables (inherited)
- Single file; inline everything; no webfont URLs; WhatsApp's own palette (#008069 header,
  #EFEAE2 wallpaper, #DCF8C6 outgoing, #25D366 accents) — this subject legitimately commits
  to WhatsApp's light look; keep text/AA contrast on the wallpaper.
- `prefers-reduced-motion` fully neutralizes packets, marching ants, receive animations.
- Wide canvas lives in an `overflow:auto` viewport (hidden scrollbar chrome); body never
  scrolls sideways. Zoom 0.5×–2× + drag with live rewiring + Reset layout, as in the
  sibling skill.
- Content is real: verbatim template bodies, real sample values, real states. A map card
  whose copy differs from the live estate is a defect to reconcile (SSOT discipline).

## Build steps
1. `Skill(artifact-design)` → 3-line plan. Gather the CURRENT map content (fetch the live
   artifact — never rebuild from a stale local copy; compare date stamps).
2. Model columns as one `.stage` grid (or several panels); every message card a `.node`
   with an id; declare ALL taps in `data-edges` (`:live` wired-live, `:build` being built,
   `:design` intended).
3. Run the build-time wiring audit. Wire rule-clear gaps as `design` edges; leave the rest
   UNWIRED and collect them as owner questions.
4. Paste `references/flow-engine.js` inline (wiring + phone-stamper + nav + validation +
   zoom/drag — modules activate on their markup).
5. Verify in a real browser (Playwright): phone chrome renders, a button click centers and
   pulses its target, the audit pill count matches your build-time audit, reduced-motion
   is static, phone-width has no sideways body scroll.
6. Publish with `Artifact` — pass `url` to update the existing map in place (stable
   favicon); then report the unwired list + questions to the owner.

## Reference
- `references/flow-engine.js` — the drop-in engine: wiring/packets, WhatsApp phone-stamper,
  tap-to-navigate, wiring-audit overlay, zoom/drag. Each module documents its required markup.
- Worked example: the PIFS map (artifact 18a28208, "PIFS WhatsApp — the conversation, card
  by card") — 80+ cards, 6 columns, SSOT for the PIFS Wati estate (§6c of gorefer CLAUDE.md).
