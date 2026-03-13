---
name: html-prototype
description: >
  Generate reusable single-file HTML prototypes with design tokens, Nielsen's
  usability heuristics validation, and PRD traceability annotations. Used for
  quick stakeholder demos before full implementation.
triggers:
  - html prototype
  - prototype page
  - stakeholder demo
  - ui mockup
  - single file html
  - quick prototype
  - clickable prototype
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<PRD/spec file path, screen name, or feature description>"
---

# HTML Prototype — Single-File Stakeholder Demo

Generate a self-contained, mobile-responsive HTML prototype with design tokens, Nielsen's heuristics compliance, and PRD traceability.

**Input:** $ARGUMENTS

---

## STEP 1: Parse PRD/Spec for Screens

Scan the provided PRD, spec, or feature description to extract screens and requirements:

| Extract | Source | Example |
|---------|--------|---------|
| Screen list | PRD sections, user stories | Login, Dashboard, Settings |
| Acceptance criteria | Story ACs, requirements | AC-001: User can reset password |
| User flows | Flow diagrams, step descriptions | Login → OTP → Dashboard |
| Data fields | Field lists, form specs | email (required), name (optional) |
| Actions/CTAs | Button labels, interactions | "Submit", "Cancel", "Next" |

Build a requirements traceability map before generating any HTML:

```markdown
## Screen Extraction

| Screen | Source Section | Acceptance Criteria | Priority |
|--------|--------------|---------------------|----------|
| Login | PRD §2.1 | AC-001, AC-002 | Must-have |
| Dashboard | PRD §3.1 | AC-010, AC-011 | Must-have |
| Settings | PRD §4.2 | AC-020 | Nice-to-have |
```

---

## STEP 2: Select Design Style

Choose a visual style based on the project context. Define all values as CSS custom properties (design tokens):

```css
:root {
  /* --- Color Tokens --- */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-secondary: #64748b;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-error: #dc2626;
  --color-bg: #ffffff;
  --color-bg-subtle: #f8fafc;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-border: #e2e8f0;

  /* --- Typography Tokens --- */
  --font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;

  /* --- Spacing Tokens --- */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
  --space-3xl: 4rem;

  /* --- Layout Tokens --- */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  --max-width: 1200px;
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
}
```

Adjust token values to match brand guidelines if provided. CDN imports are allowed for fonts only (e.g., Google Fonts).

---

## STEP 3: Generate Single-File HTML

Produce a single `.html` file with all CSS inline in `<style>` and all JS inline in `<script>`. Structure:

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project] — Prototype</title>
  <!-- CDN font imports only (no other external deps) -->
  <style>
    /* Reset */
    /* Design tokens (:root) */
    /* Layout (mobile-first) */
    /* Components */
    /* Screen-specific styles */
    /* Responsive breakpoints (@media) */
  </style>
</head>
<body>
  <!-- Screen markup with data-req attributes -->
  <script>
    /* Screen navigation */
    /* Interactive behaviors */
    /* State management (minimal) */
  </script>
</body>
</html>
```

### Mobile-First Responsive Rules

- Base styles target mobile (320px+)
- Use `@media (min-width: var(--breakpoint-md))` for tablet+
- Use `@media (min-width: var(--breakpoint-lg))` for desktop+
- Navigation collapses to hamburger menu on mobile
- Touch targets minimum 44x44px
- Font sizes scale with `clamp()` where appropriate

### Multi-Screen Navigation

For prototypes with multiple screens, use JS-driven screen switching:

```javascript
function showScreen(screenId) {
  document.querySelectorAll('[data-screen]').forEach(s => s.hidden = true);
  document.querySelector(`[data-screen="${screenId}"]`).hidden = false;
  history.pushState(null, '', `#${screenId}`);
}
```

Each screen is a `<section data-screen="screen-name">` element. A nav bar or tab bar links between screens.

---

## STEP 4: Apply Nielsen's 10 Heuristics Checklist

After generating the HTML, validate against all 10 heuristics. Fix violations before delivering.

| # | Heuristic | Validation Check | Fix If Missing |
|---|-----------|-----------------|----------------|
| 1 | Visibility of system status | Loading states, active nav indicators, form submission feedback | Add spinners, progress bars, active states |
| 2 | Match between system and real world | Labels use user language (not dev jargon), familiar icons | Rewrite labels, use standard iconography |
| 3 | User control and freedom | Back buttons, cancel actions, undo for destructive ops | Add cancel/back on every modal and form |
| 4 | Consistency and standards | Same button styles, consistent nav position, uniform spacing | Enforce design tokens throughout |
| 5 | Error prevention | Required field markers, input constraints, confirmation dialogs | Add `required`, `pattern`, confirm modals |
| 6 | Recognition rather than recall | Visible labels (not just placeholders), breadcrumbs, contextual help | Replace placeholder-only inputs with labels |
| 7 | Flexibility and efficiency | Keyboard navigation, logical tab order, shortcut hints | Add `tabindex`, `accesskey` where useful |
| 8 | Aesthetic and minimalist design | No decorative-only elements, clear visual hierarchy, whitespace | Remove clutter, increase spacing |
| 9 | Help users recognize and recover from errors | Inline validation messages, descriptive error text | Add `aria-describedby` error messages |
| 10 | Help and documentation | Tooltips on complex fields, contextual guidance | Add `title` attributes, help icons |

Include a heuristics summary in the prototype footer (visible in dev/demo mode):

```html
<!-- Heuristics compliance (toggle with ?heuristics=show) -->
<aside id="heuristics-panel" hidden>
  <h3>Nielsen's Heuristics — Compliance</h3>
  <ul>
    <li>H1 System Status: PASS — loading states on all async actions</li>
    <!-- ... one entry per heuristic ... -->
  </ul>
</aside>
```

---

## STEP 5: Add PRD Traceability Annotations

Tag every interactive element and content block with `data-req` attributes linking back to the PRD acceptance criteria:

```html
<form data-req="AC-001" data-req-title="User can log in with email and password">
  <input type="email" data-req="AC-001.1" placeholder="Email" required>
  <input type="password" data-req="AC-001.2" placeholder="Password" required>
  <button type="submit" data-req="AC-001.3">Sign In</button>
</form>

<section data-req="AC-010" data-req-title="Dashboard shows summary metrics">
  <div class="metric-card" data-req="AC-010.1">...</div>
</section>
```

Add a traceability overlay toggle (activated via `?trace=show` query param or keyboard shortcut):

```javascript
function toggleTraceability() {
  document.querySelectorAll('[data-req]').forEach(el => {
    el.classList.toggle('trace-highlight');
    // Show data-req value as an overlay badge
  });
}
```

When the overlay is active, each annotated element displays its `data-req` ID as a colored badge, making it easy for stakeholders to reference specific requirements during review.

---

## STEP 6: Interactive Walkthrough

After generating the prototype, present a structured walkthrough:

```markdown
## Prototype Walkthrough

**File:** `prototype-<project>.html`
**Screens:** <N> screens generated
**Requirements covered:** <N> / <total> acceptance criteria

### Screen-by-Screen Summary

| Screen | Key Elements | Requirements | Heuristics Notes |
|--------|-------------|-------------|-----------------|
| Login | Email/password form, social login buttons | AC-001, AC-002 | H5: required fields marked |
| Dashboard | Metric cards, recent activity table | AC-010, AC-011 | H1: loading skeleton added |

### How to Demo

1. Open `prototype-<project>.html` in any modern browser
2. Navigate between screens using the top nav bar
3. Append `?trace=show` to the URL to see requirement annotations
4. Append `?heuristics=show` to view the heuristics compliance panel
5. Resize the browser window to test responsive breakpoints

### Requirements Not Yet Covered

| Requirement | Reason | Recommendation |
|-------------|--------|---------------|
| AC-030 | Requires real API data | Add in next iteration with mock data |
```

---

## MUST DO

- Always extract and map requirements from the PRD/spec before generating HTML
- Always define colors, typography, and spacing as CSS custom properties (design tokens)
- Always use mobile-first responsive design with min-width breakpoints
- Always validate against all 10 of Nielsen's heuristics after generation
- Always add `data-req` attributes to trace HTML elements back to acceptance criteria
- Always include a traceability overlay toggle for stakeholder reviews
- Always use semantic HTML elements (`<nav>`, `<main>`, `<section>`, `<form>`, `<button>`)
- Always ensure touch targets are at least 44x44px
- Always include a walkthrough summary with demo instructions

## MUST NOT DO

- MUST NOT use any external CSS or JS libraries (CDN fonts are the only exception)
- MUST NOT split output across multiple files — the prototype MUST be a single HTML file
- MUST NOT use placeholder-only form inputs — always pair with visible `<label>` elements
- MUST NOT skip heuristic validation — prototypes that violate basic usability waste stakeholder time
- MUST NOT include real data, credentials, or API keys in prototype content
- MUST NOT use fixed pixel widths that break on mobile viewports
- MUST NOT generate screens that are not traceable to at least one PRD requirement
