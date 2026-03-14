# Stage 4: Interactive HTML UI Demo — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to generate a multi-file, interactive HTML prototype (website or mobile app) with realistic sample data, a shared design system, and an implementation mapping doc — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 1 (PRD) + Stage 3 (Scaffold — for design context)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 4: INTERACTIVE HTML DEMO                    │
 └─────────────────────────────────────────────────────────────────┘

        ┌───────────────────────┐
        │  Read PRD from ST1    │
        │  + Scaffold from ST3  │
        └───────────┬───────────┘
                    │
                    ▼
  ┌──────────────────────────────┐
  │  Skip Check                  │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  CLI-only project?           │
  │  ┌─── YES ──→ skip stage     │
  │  └─── NO  ──→ continue       │
  └──────────────┬───────────────┘
                 │ (NO)
                 ▼
  ┌──────────────────────────────┐
  │  Sample Data Generation      │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  • Realistic mock data       │
  │  • Per user story dataset    │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  HTML Prototype Build        │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  html-prototype skill        │
  │  • One HTML file per screen  │
  │  • shared.css (design system)│
  │  • shared.js (state + data)  │
  │  • index.html (screen map)   │
  │  • IMPL-MAPPING.md           │
  │  • Dark mode (light/dark)    │
  │  • data-req="US-xxx" attrs   │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  UI/UX Enrichment            │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  ui-ux-pro-max skill         │
  │  • Component patterns        │
  │  • Interaction design        │
  │  • Stakeholder overlay       │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Validation Gate             │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • a11y-audit (axe-core)     │
  │  • Nielsen's 10 heuristics   │
  │  • Performance budget check  │
  │  • verify-screenshots        │
  └──────────────┬───────────────┘
                 │
            PASS │ / FAIL → retry
                 ▼
       ┌──────────────────┐
       │   Demo Output     │
       │   ████████████████ │
       └──────────────────┘
```

### Diagram B — I/O Artifact Contract

```
                          INPUTS
 ┌──────────────────────────────────────────────┐
 │                                              │
 │  ┌──────────────────┐ ┌──────────────────┐   │
 │  │ From ST1: prd.md │ │ From ST3:        │   │
 │  │  • User stories  │ │  • Design context│   │
 │  │  • Requirement   │ │  • Project type  │   │
 │  │    IDs (US-xxx)  │ │  • Stack info    │   │
 │  └────────┬─────────┘ └────────┬─────────┘   │
 │           │                    │              │
 └───────────┼────────────────────┼──────────────┘
             │                    │
             └─────────┬──────────┘
                       │
                       ▼
        ┌───────────────────────────────┐
        │                               │
        │  ███ STAGE 4: HTML DEMO ███   │
        │                               │
        │  html-prototype               │
        │  ui-ux-pro-max                │
        │  a11y-audit                   │
        │  verify-screenshots           │
        │                               │
        └──────────────┬────────────────┘
                       │
            ┌──────────┼──────────┐
            │          │          │
            ▼          ▼          ▼
 ┌──────────────┐┌───────────┐┌──────────────┐┌──────────────┐
 │ index.html + ││screenshots││ shared.css + ││ IMPL-        │
 │ N screen     ││ (PNG)     ││ shared.js    ││ MAPPING.md   │
 │ HTML files   ││           ││ (design      ││ (CSS→Compose │
 │ (data-req    ││           ││  system +    ││  or SwiftUI  │
 │  attrs)      ││           ││  mock data)  ││  mapping)    │
 └──────┬───────┘└─────┬─────┘└──────┬───────┘└──────┬───────┘
        │              │             │               │
        ▼              ▼             ▼               ▼
  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────┐
  │ ST7 Impl │  │ ST9 Revw  │  │ ST7 Impl │  │ ST7 Impl     │
  │ (UI ref) │  │ (visual   │  │ (tokens  │  │ (platform    │
  │          │  │  ref)     │  │  source) │  │  impl spec)  │
  └──────────┘  └───────────┘  └──────────┘  └──────────────┘
                   OUTPUTS
```

## Execution Workflow

When dispatched by the pipeline orchestrator, execute these steps in order.

### Step 1: Read Upstream Artifacts

```
Read docs/plans/<feature>-prd.md          ← From Stage 1 (user stories, ACs, requirement IDs)
Read <project_root>/                       ← From Stage 3 (detect stack, design context)
```

Extract from the PRD:
- All user stories (US-xxx) and acceptance criteria (AC-xxx)
- Project type (website vs mobile app vs both)
- Target platform (Android/Compose, iOS/SwiftUI, React/Web, etc.)
- Any branding/design guidelines mentioned

### Step 2: Generate Design System via `ui-ux-pro-max`

Run **before** generating HTML — the design system informs the prototype's tokens.

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system -p "<project_name>"
```

Use the output to set color palette, typography, spacing, and style direction for `shared.css`.

If the PRD specifies a design system (Material 3, iOS HIG, etc.), use that as the primary source and supplement with `ui-ux-pro-max` for gaps.

### Step 3: Generate HTML Prototype via `html-prototype`

Invoke the `html-prototype` skill with the PRD path:

```
/html-prototype <path-to-prd.md>
```

This produces all screen files, `shared.css`, `shared.js`, `index.html`, and `IMPL-MAPPING.md` in `demos/<feature>/`.

### Step 4: Data Visualization (Conditional — `d3-viz`)

If the PRD contains dashboard screens, analytics pages, charts, or data visualization requirements:

```
/d3-viz <chart-requirements from PRD>
```

Embed the generated chart components into the relevant screen HTML files. If no data visualization is needed, skip this step.

### Step 5: Accessibility Audit via `a11y-audit`

Run on the generated prototype directory:

```
/a11y-audit demos/<feature>/index.html --scope site --threshold 90
```

Fix all critical and serious violations before proceeding. Re-run until the audit passes.

### Step 6: Screenshot Capture via `verify-screenshots`

Capture screenshots for downstream stages:

```bash
# Serve the prototype
npx serve demos/<feature>/ -l 3000 &

# Capture each screen
npx playwright screenshot --browser chromium http://localhost:3000/index.html docs/stages/screenshots/stage-4/index.png
# Repeat for each screen file
```

Then verify with:

```
/verify-screenshots docs/stages/screenshots/stage-4/
```

### Step 7: Gate Validation

Verify all artifacts exist:

```bash
test -f demos/<feature>/index.html          # Screen map
test -f demos/<feature>/shared.css          # Design system CSS
test -f demos/<feature>/shared.js           # State + mock data
test -f demos/<feature>/IMPL-MAPPING.md     # Platform mapping
ls demos/<feature>/*.html | wc -l           # At least 2 screen files
ls docs/stages/screenshots/stage-4/*.png | wc -l  # At least 1 screenshot
```

Return structured JSON to orchestrator:

```json
{
  "gate": "PASSED",
  "artifacts": {
    "screens": "demos/<feature>/index.html",
    "design_system_css": "demos/<feature>/shared.css",
    "design_system_js": "demos/<feature>/shared.js",
    "impl_mapping": "demos/<feature>/IMPL-MAPPING.md",
    "screenshots": "docs/stages/screenshots/stage-4/"
  },
  "decisions": [],
  "blockers": [],
  "summary": "Generated N-screen prototype with design system, IMPL-MAPPING, and screenshots. a11y score: X/100."
}
```

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Multi-file HTML prototype (one file per screen) | `html-prototype` skill (Step 3) | ✅ Covered | — |
| 2 | Realistic sample data generation | Stage 4 prompt (Step 2) | ✅ Covered | — |
| 3 | Design system / UI patterns | `ui-ux-pro-max` skill | ✅ Covered | — |
| 4 | Responsive design (4 breakpoints) | Stage 4 prompt (MUST HAVE) | ✅ Covered | — |
| 5 | Dark mode | Stage 4 prompt (MUST HAVE) | ✅ Covered | — |
| 6 | Accessibility (ARIA, contrast, focus) | Stage 4 prompt (MUST HAVE) | ✅ Covered | **WCAG 2.1 AA** |
| 7 | User story → UI component mapping | Stage 4 prompt (Step 3: "for EACH PRD user story") | ✅ Covered | — |
| 8 | Visual regression / screenshot capture | `verify-screenshots` skill | ✅ Covered | — |
| 9 | Design tokens / design system constants | `html-prototype` skill (CSS custom properties for tokens) | ✅ Covered | **Design Tokens (W3C)** |
| 10 | Stakeholder feedback mechanism | `html-prototype` skill (requirement overlay toggle) | ✅ Covered | **User-Centered Design (ISO 9241-210)** |
| 11 | PRD traceability in demo | `html-prototype` skill (data-req attributes on components) | ✅ Covered | **Requirements Traceability** |
| 12 | Usability heuristic evaluation | `html-prototype` skill (Nielsen's 10 heuristics checklist) | ✅ Covered | **Nielsen's 10 Usability Heuristics** |
| 13 | Performance budget for demo | `html-prototype` skill (file size + load time checks) | ✅ Covered | **Web Performance** |
| 14 | Mobile-first / progressive enhancement | `html-prototype` skill (mobile-responsive by default) | ✅ Covered | **Progressive Enhancement** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **WCAG 2.1 AA** | Accessibility compliance | ✅ `a11y-audit` skill with axe-core + Lighthouse automated checking |
| **Design Tokens (W3C)** | Centralized design constants (colors, spacing, typography) | ✅ CSS custom properties in `html-prototype` |
| **ISO 9241-210** | User-centered design, stakeholder feedback loops | ✅ Requirement overlay toggle in `html-prototype` |
| **Nielsen's Heuristics** | Visibility of system status, error prevention, recognition over recall, etc. | ✅ 10-heuristic validation checklist in `html-prototype` |
| **Progressive Enhancement** | Core content accessible without JS, enhanced with JS | ✅ Mobile-responsive default layout in `html-prototype` |

## Gap Proposals

### Gap 4.1: `html-prototype` skill (Priority: P2)

**Problem it solves:** Prototype generation logic is embedded in Stage 4 prompt — not reusable for ad-hoc prototyping outside the pipeline.

**What it needs:**
- Design token extraction from `ui-ux-pro-max` output
- Nielsen's 10 Usability Heuristics checklist in verification step
- PRD traceability annotations (`data-us="US-001"` attributes on components)
- Stakeholder comment mode (toggle overlay showing requirement IDs)

**Existing coverage:** Stage 4 prompt handles HTML construction well. `ui-ux-pro-max` provides design guidance. `verify-screenshots` handles visual validation.

### Gap 4.2: Automated accessibility audit in demo gate (Priority: P2)

**Problem it solves:** Accessibility checking relies on manual ARIA/contrast review — error-prone for autonomous operation.

**What to add:**
- Integrate axe-core CDN or Lighthouse CI into verification step
- Automated color contrast ratio checking
- Tab order verification

**Existing coverage:** WCAG mentioned in prompt but no automated tooling.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `demos/<feature>/index.html` + N screen HTML files | Stakeholder review (human), Stage 7 (Impl — UI reference) | One HTML file per screen, organized by flow prefix |
| `demos/<feature>/shared.css` + `shared.js` | Stage 7 (Impl — design token source of truth) | Shared design system (CSS custom properties + JS state/mock data) |
| `demos/<feature>/IMPL-MAPPING.md` | Stage 7 (Impl — platform implementation spec) | CSS-to-Compose / CSS-to-SwiftUI / CSS-to-React mapping |
| `docs/stages/screenshots/stage-4/` | Stage 9 (Review — visual reference) | PNG images |

## Research Targets

- **GitHub**: `html prototype multi-screen`, `material 3 html demo`, `mobile app html mockup`
- **Reddit**: r/Frontend — "HTML prototype before coding", r/webdev — "stakeholder demo techniques", r/androiddev — "HTML mockup before Compose"
- **Twitter/X**: `v0.dev prototype`, `html app prototype`, `mobile UI html demo`

## Stack Coverage

Universal — HTML prototype is stack-agnostic. The demo uses vanilla CSS + JS with no external frameworks (CDN fonts only). Works for both website and mobile app prototypes. Mobile apps are simulated via a phone-frame wrapper with status bar and bottom nav. The `IMPL-MAPPING.md` bridges the prototype to the target platform (Compose for Android, SwiftUI for iOS, React/MUI for web).

## Autonomy Verdict

**✅ Can run autonomously.** All 14 capabilities covered. Execution workflow defines the exact skill invocation sequence: `ui-ux-pro-max` (design system) → `html-prototype` (screens + design tokens + IMPL-MAPPING) → `d3-viz` (conditional, for dashboards) → `a11y-audit` (WCAG compliance) → `verify-screenshots` (visual capture). Pipeline-orchestrator artifact contract validates all 5 output types. Skip condition covers CLI, library, API-only, backend, data pipeline, and infrastructure projects.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P2 gaps resolved: `html-prototype` and `a11y-audit` skills created — design tokens, Nielsen's heuristics, PRD traceability, WCAG automated audit all ✅ |
| 2026-03-14 | Added execution workflow (7-step skill sequencing), expanded artifacts_out to 5 types, broadened skip_when to cover API/backend/pipeline/infra projects, resolved Tailwind/Alpine contradiction in STAGE-DEPENDENCIES.md, added conditional d3-viz integration |
