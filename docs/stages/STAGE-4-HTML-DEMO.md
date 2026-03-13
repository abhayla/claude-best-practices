# Stage 4: Interactive HTML UI Demo — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to generate a standalone, self-contained HTML prototype with realistic sample data that validates the product vision — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 1 (PRD) + Stage 3 (Scaffold — for design context)
> **Last Updated:** 2026-03-13
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
  │  • Single-file HTML          │
  │  • Tailwind CSS + Alpine.js  │
  │  • Design tokens (CSS vars)  │
  │  • Dark mode toggle          │
  │  • 4 responsive breakpoints  │
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
 ┌──────────────┐┌───────────┐┌──────────────┐
 │ demo.html    ││screenshots││ Design       │
 │ (single-file ││ (PNG)     ││ decisions    │
 │  prototype   ││           ││ (colors,     │
 │  with data-  ││           ││  components) │
 │  req attrs)  ││           ││              │
 └──────┬───────┘└─────┬─────┘└──────┬───────┘
        │              │             │
        ▼              ▼             ▼
  ┌──────────┐  ┌───────────┐  ┌──────────┐
  │ ST7 Impl │  │ ST9 Revw  │  │ ST7 Impl │
  │ (UI ref) │  │ (visual   │  │ (UI impl │
  │          │  │  ref)     │  │  guide)  │
  └──────────┘  └───────────┘  └──────────┘
                   OUTPUTS
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Single-file HTML prototype generation | Stage 4 prompt (Step 3) | ✅ Covered | — |
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
| `demos/<feature>-demo.html` | Stakeholder review (human), Stage 7 (Impl — as UI reference) | Single HTML file |
| `docs/stages/screenshots/stage-4/` | Stage 9 (Review — visual reference) | PNG images |
| Design decisions (color palette, component patterns) | Stage 7 (Impl — UI implementation) | Documented in stage doc |

## Research Targets

- **GitHub**: `single file html prototype`, `tailwind dashboard template` >1000 stars, `alpine.js demo`
- **Reddit**: r/Frontend — "HTML prototype before coding", r/webdev — "stakeholder demo techniques"
- **Twitter/X**: `v0.dev prototype`, `single file HTML demo`, `tailwind prototype`

## Stack Coverage

Universal — HTML prototype is stack-agnostic. The demo uses CDN libraries (Tailwind, Alpine.js) regardless of the project's actual frontend stack. Stack-specific UI patterns (Android Material, iOS HIG) would need separate demo approaches but are out of scope for an HTML prototype.

## Autonomy Verdict

**✅ Can run autonomously.** `html-prototype` skill adds design tokens, Nielsen's heuristics validation, PRD traceability annotations, and mobile-responsive layout. `a11y-audit` skill adds automated WCAG 2.1 AA compliance checking with axe-core and Lighthouse. Combined with existing `ui-ux-pro-max` and `verify-screenshots`, all 14 capabilities now ✅.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P2 gaps resolved: `html-prototype` and `a11y-audit` skills created — design tokens, Nielsen's heuristics, PRD traceability, WCAG automated audit all ✅ |
