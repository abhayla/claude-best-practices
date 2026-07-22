---
name: modern-data-pipeline-diagram
description: >
  Build the animated MODERN DATA PIPELINE diagram — Collect → Ingest → Store → Compute →
  Consume (the ByteByteGo five-stage model) — as a single self-contained HTML artifact:
  nodes connected by continuously-flowing SVG connectors (travelling packets +
  marching-ants strokes), boxes with float / glow / pulse / hover-lift spatial effects, a
  live ambient background field, scroll-reveal, and full prefers-reduced-motion support.
  Use when the user asks for the modern data pipeline diagram, a data-platform /
  data-architecture picture (lake, warehouse, lakehouse, Kafka, batch/stream, BI/ML), or
  any variant of it. The animation mechanics generalize: for a non-pipeline animated
  diagram, reuse the engine here with a different node/edge model. Not for static Mermaid
  (use a plain ```mermaid block) or charts of quantitative data (use the dataviz skill).
---

# Modern data pipeline diagram

Produce ONE self-contained HTML file (inline CSS + JS, no external fetches — Artifact CSP blocks
CDNs) that renders a boxes-and-arrows diagram where the arrows continuously flow and the boxes
have ambient spatial motion. Publish it with the `Artifact` tool. First load `artifact-design`
to calibrate palette/type/treatment to the subject — this skill owns the *animation mechanics*,
that skill owns the *visual identity*.

## When to use / not use
- USE: "the modern data pipeline diagram", "data platform / data architecture picture"
  (lake / warehouse / lakehouse, Kafka, batch + stream, BI/ML), or any animated
  boxes-and-arrows request — "wiring map", "flow diagram with moving arrows", "make it look
  alive". With no other subject stated, the CANONICAL SUBJECT below is the default.
- NOT: quantitative charts → `dataviz`; a static graph where motion adds nothing → plain
  ```mermaid fenced block (artifacts render it natively); a UI mockup → `frontend-design`.

## The canonical subject — the modern data pipeline (default node/edge model)

Five stages (ByteByteGo model, captured 2026-07-22: "A Modern Data Pipeline: From Raw Data
to Business Value"), rendered as five vertical tiers with a stage rail. Two edge semantics:
`live` = batch path (cool/teal), `build` = streaming path (warm) — reusing the engine's two
packet-colored kinds.

| Stage | Nodes | Edges out |
|---|---|---|
| 1 Collect | `data-stores`, `data-streams`, `applications` | stores→load (live), apps→load (live), streams→queue (build) |
| 2 Ingest | `data-load`, `event-queue` (Kafka · Event Hubs · Kinesis) | load→lake + load→warehouse (live); queue→lake + queue→lakehouse (build) |
| 3 Store | `data-lake`, `data-warehouse`, `lakehouse` | lake→batch-proc + warehouse→batch-proc (live); lake→stream-proc + lakehouse→stream-proc (build) |
| 4 Compute | `batch-proc`, `stream-proc` | batch→data-science + batch→business-intelligence (live); stream→self-service + stream→ml-services (build) |
| 5 Consume | `data-science`, `business-intelligence`, `self-service`, `ml-services` | — |

Payoff strip under the diagram (the post's claims): real-time decision making · scalable
analytics · reliable pipelines · AI & ML readiness · faster business insights. Credit the
model: "Pipeline model after ByteByteGo". A variant subject (user supplies different
stages/nodes) swaps this table, nothing else.

## The core mechanic — a JS wiring engine (the load-bearing idea)
Do NOT hand-author SVG path coordinates. Lay out nodes as normal responsive HTML (grid/flex) with
`id`s, put an absolutely-positioned `<svg class="wires" data-edges="a>b:live, b>c:build">` behind
them, and let JS draw + animate the connectors AFTER layout, re-running on resize / font-load /
scroll-reveal. This keeps arrows correct at every breakpoint.

Each edge = `from>to` with an optional `:kind` (live / build / design or your semantic classes).
The engine: computes the two nodes' rects relative to the stage, picks edge anchor points on the
dominant axis (horizontal → right↔left, vertical → bottom↔top), builds a cubic-Bézier `path`, adds
`class="flowing <kind>"` (a `stroke-dasharray` + `@keyframes dash` marching stroke), and appends an
SVG `<circle class="pkt">` that travels the path via `<animateMotion><mpath href="#pathId"/>` — a
real "packet" moving along the wire, no JS animation loop. Stagger `begin` per edge.

Copy the engine from `references/wiring-engine.js` (drop it inline in a `<script>`). It exposes
`wireAll()` — call it on `load`, `resize` (debounced), `document.fonts.ready`, and after each
scroll-reveal. Guard everything behind a `prefers-reduced-motion` check: no packets, no marching,
static stroke, reveals shown immediately.

## Spatial effects on the boxes (every box, tastefully)
- **Float**: `@keyframes float{50%{transform:translateY(-6px)}}` on `.node`, with a per-node
  `--fdel` (staggered delay) and occasional `--fdur` variation so they don't breathe in lockstep.
- **Glow pulse**: a `::after` ring `box-shadow` on state nodes (`.live`, `.build`) animating opacity
  — colored by the semantic token, never the neutral.
- **Hover lift**: `transform: translateY(-5px) scale(1.01)` + accent border + deeper shadow, with a
  cubic-bezier transition. Makes interactive-looking nodes feel interactive.
- **Entrance**: `.reveal` → `.in` via `IntersectionObserver` (fade + rise, staggered by section).
- **Ambient field** (optional hero): a Canvas particle-and-line constellation tinted to the accent
  — the "signal is alive" backdrop. Cheap, `devicePixelRatio`-aware, reseeds on resize. Skip under
  reduced-motion.

## Non-negotiables (inherited from artifact-design)
- Single file; inline everything; no webfont URLs (use a strong system stack or a data-URI face).
- Semantic color (live/warning/build) is SEPARATE from the accent hue; pick neutrals with a slight
  hue bias toward the accent, not pure grey.
- A committed single-world (e.g. a dark "operations console") is a legitimate choice for a
  glowing/animated subject — state it deliberately; otherwise do token-based light+dark.
- Wide content in `overflow-x:auto`; the body never scrolls sideways. Tabular numerals for data.
- `prefers-reduced-motion` MUST fully neutralize motion. Keyboard focus visible.
- Content is real (no lorem); copy written from the reader's side, labels by what people recognize.

## Build steps
1. `Skill(artifact-design)` → write a 3-line plan (color / type / layout) grounded in the subject.
2. Model the diagram as sections ("panels"), each a `.stage` with its own `<svg class="wires">`
   and node grid; declare edges in `data-edges`. Keep each panel readable — many small wired
   panels beat one giant unreadable graph.
3. Paste the wiring engine + effect CSS; assign `.live/.build/.design` (or your semantics) + `--fdel`.
4. Publish with `Artifact` (keep a stable `favicon`; pass `url` to update an existing diagram in place).
5. Verify: resize to a phone width (arrows re-route, no sideways scroll), and confirm reduced-motion
   renders static-but-complete.

## Interaction layer (default ON for this skill's output)
The engine file also ships an optional zoom + drag module (activates only when its markup exists —
see the comment block in `references/wiring-engine.js`): zoom 0.5×–2× via +/−/1:1 buttons and
ctrl+wheel (viewport height is compensated so zoom never overlaps later sections), and pointer-drag
on every `.node` (mouse + touch) with offsets stored in `left/top` — the float animation's transform
is untouched — and `wireAll()` re-run live during the drag so connectors stay attached; a
"Reset layout" button clears all offsets. Zoom needs no engine change: the wires' viewBox math is
scale-invariant. Include the controls + `#viewport`/`#zoomable` wrappers in every diagram this skill
produces unless the user asks for a static picture.

## Reference
- `references/wiring-engine.js` — the drop-in connector/packet engine (`wireAll()` + ambient field
  + the optional zoom/drag interaction layer).
- Worked example: the PIFS WhatsApp "living estate" map (artifact 2dc71e77) — 6 wired panels,
  flowing packets, breathing nodes, committed dark console world.
