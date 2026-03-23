---
name: html-prototype
description: >
  Generate multi-file working HTML prototypes for websites or mobile apps.
  Produces a shared design system (CSS + JS), one HTML file per screen,
  an index page as screen map, and an implementation mapping doc.
  Use when creating stakeholder demos, clickable prototypes, or UI mockups.
triggers:
  - html prototype
  - prototype page
  - stakeholder demo
  - ui mockup
  - working prototype
  - clickable prototype
  - mobile app prototype
  - app demo
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<PRD/spec file path, screen name, or feature description>"
version: "1.0.0"
type: workflow
---

# HTML Prototype — Multi-File Working Demo

Generate a fully interactive, multi-file HTML prototype for a website or mobile app. The prototype serves as both a stakeholder demo and the implementation specification for the target platform.

**Input:** $ARGUMENTS

---

## STEP 1: Parse PRD/Spec for Screens

Scan the provided PRD, spec, or feature description to extract all screens:

| Extract | Source | Example |
|---------|--------|---------|
| Screen list | PRD sections, user stories | Splash, Login, OTP, Home, Settings |
| Acceptance criteria | Story ACs, requirements | AC-001: User can log in with phone + OTP |
| User flows | Flow diagrams, step descriptions | Splash → Phone → OTP → Onboarding → Home |
| Data fields | Field lists, form specs | phone (required), OTP (6 digits) |
| Actions/CTAs | Button labels, interactions | "Send OTP", "Verify", "Skip" |
| Modals/sheets | Bottom sheets, dialogs, alerts | Swap recipe, Delete confirmation, Share |

Build a requirements traceability map before generating any HTML:

```markdown
## Screen Extraction

| Screen | File Name | Source Section | Acceptance Criteria | Priority |
|--------|-----------|---------------|---------------------|----------|
| Splash | auth-splash.html | PRD §1.1 | AC-001 | Must-have |
| Phone Entry | auth-phone.html | PRD §1.2 | AC-002, AC-003 | Must-have |
| Home | main-home.html | PRD §3.1 | AC-010, AC-011 | Must-have |
| Settings | settings-main.html | PRD §5.1 | AC-040 | Must-have |
| Delete Dialog | modal-delete.html | PRD §5.3 | AC-045 | Nice-to-have |
```

### File Naming Convention

Use prefixed names that group screens by flow:

| Prefix | Screen Type | Examples |
|--------|------------|---------|
| `auth-` | Authentication flow | `auth-splash.html`, `auth-phone.html`, `auth-otp.html` |
| `onboarding-` | Onboarding steps | `onboarding-step1-household.html` |
| `main-` | Primary tab screens | `main-home.html`, `main-chat.html` |
| `detail-` | Detail/drill-down views | `detail-recipe.html`, `detail-cooking-mode.html` |
| `feature-` | Feature-specific screens | `feature-pantry.html`, `feature-achievements.html` |
| `settings-` | Settings screens | `settings-main.html`, `settings-dietary.html` |
| `modal-` | Bottom sheets, dialogs | `modal-swap-sheet.html`, `modal-delete.html` |

---

## STEP 2: Build the Shared Design System

Create two shared files that every screen imports. These are the single source of truth for the entire prototype's look and behavior.

### 2.1: `shared.css` — Design Tokens + Components

Define the complete design system as CSS custom properties with light AND dark theme support:

```css
/* Light theme (default) */
:root,
[data-theme="light"] {
  /* Primary palette */
  --primary: #2563eb;
  --on-primary: #FFFFFF;
  --primary-container: #E0EDFF;
  --on-primary-container: #001A40;

  /* Secondary palette */
  --secondary: #64748b;
  --on-secondary: #FFFFFF;
  --secondary-container: #E2E8F0;
  --on-secondary-container: #1E293B;

  /* Tertiary palette */
  --tertiary: #7A4E22;
  --on-tertiary: #FFFFFF;
  --tertiary-container: #FFDDB8;
  --on-tertiary-container: #2E1500;

  /* Error */
  --error: #BA1A1A;
  --on-error: #FFFFFF;
  --error-container: #FFDAD6;
  --on-error-container: #410002;

  /* Background & Surface */
  --background: #FAFAFA;
  --on-background: #1C1B1F;
  --surface: #FFFFFF;
  --on-surface: #1C1B1F;
  --surface-variant: #F1F5F9;
  --on-surface-variant: #49454F;

  /* Outline */
  --outline: #7A757F;
  --outline-variant: #CAC4D0;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.08);
  --shadow-md: 0 2px 6px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.08), 0 16px 48px rgba(0,0,0,0.06);

  /* Spacing */
  --sp-xs: 4px;  --sp-sm: 8px;  --sp-md: 16px;
  --sp-lg: 24px; --sp-xl: 32px; --sp-xxl: 48px;

  /* Shape */
  --radius-sm: 8px;  --radius-md: 16px;
  --radius-lg: 24px; --radius-full: 9999px;

  /* Typography */
  --font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;

  /* Transitions */
  --transition-fast: all 0.15s ease-out;
  --transition-normal: all 0.3s ease-out;
}

/* Dark theme */
[data-theme="dark"] {
  --primary: #93B8FF;
  --on-primary: #00306E;
  /* ... dark variants for all tokens ... */
  --background: #1C1B1F;
  --surface: #2B2930;
}
```

Adjust token values to match brand guidelines or the target platform's design system (Material 3, iOS HIG, etc.). CDN imports allowed for fonts only (e.g., Google Fonts).

Include component classes: cards, buttons, chips, text fields, bottom nav, top app bar, bottom sheets, dialogs, empty states, skeleton loaders, badges, progress indicators.

### 2.2: `shared.js` — State, Mock Data, Helpers

```javascript
// --- LocalStorage State Management ---
function getState(key, defaultVal) { /* read from localStorage with prefix */ }
function setState(key, value) { /* write to localStorage with prefix */ }
function clearAllState() { /* clear all prefixed keys */ }

// --- Theme ---
function applyTheme() { /* read dark_mode state, set data-theme attribute */ }
function toggleDarkMode() { /* toggle light/dark/system */ }

// --- Realistic Mock Data ---
// Domain-specific, not lorem ipsum. Example for a recipe app:
const MOCK_USERS = [ /* realistic user profiles */ ];
const MOCK_RECIPES = [ /* realistic items with all fields */ ];
const MOCK_NOTIFICATIONS = [ /* realistic notifications */ ];

// --- Reusable Component Renderers ---
function renderStatusBar() { /* phone status bar: time, battery, signal */ }
function renderBottomNav(activeTab) { /* bottom navigation with active state */ }
function renderTopBar(title, actions) { /* top app bar */ }

// --- Page Initialization ---
function initPage() {
  applyTheme();
  // Common setup for every page
}
```

**Mock data rules:**
- Use realistic, domain-appropriate data (real names, plausible values)
- Include enough variety to demonstrate all UI states (empty, few items, many items)
- Include edge cases (long text, special characters, missing optional fields)
- NEVER include real credentials, API keys, or PII

---

## STEP 3: Generate Screen Files

Create one HTML file per screen. Each file follows this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project] - [Screen Name]</title>
  <link rel="stylesheet" href="shared.css">
  <script src="shared.js"></script>
  <style>
    /* Screen-specific styles only (if any) */
  </style>
</head>
<body>
  <div class="phone-frame" id="app">
    <!-- For mobile apps: wrap in phone-frame -->
    <!-- For websites: use standard layout -->

    <!-- Screen content with data-req attributes -->
    <nav id="bottom-nav"></nav>
  </div>

  <script>
    initPage();
    // Screen-specific logic
    // Render shared components
    document.getElementById('bottom-nav').outerHTML = renderBottomNav('home');
  </script>
</body>
</html>
```

### Mobile App Prototype Rules

When prototyping a mobile app:
- Wrap all content in `<div class="phone-frame">` to simulate device viewport
- Include a status bar (time, battery, signal) at the top via `renderStatusBar()`
- Include bottom navigation bar via `renderBottomNav(activeTab)` on main screens
- Use `<a href="other-screen.html">` for navigation between screens (NOT JS routing)
- Touch targets minimum 44x44px
- Scrollable content area between top bar and bottom nav

### Website Prototype Rules

When prototyping a website:
- No phone frame wrapper — use full browser viewport
- Mobile-first responsive: base styles for mobile, `@media (min-width)` for tablet/desktop
- Navigation collapses to hamburger menu on mobile
- Font sizes scale with `clamp()` where appropriate
- Use `<a href="other-screen.html">` for navigation between pages

### Cross-Screen State

State persists across screens via `localStorage` through the `getState`/`setState` helpers:
- User preferences (dark mode, selected options)
- Form data entered in previous steps (onboarding flows)
- Toggled/selected items (favorites, locked items)
- Current position in multi-step flows

---

## STEP 4: Create the Index Page

`index.html` is the master screen map — the entry point for the prototype. It lists ALL screens organized by flow:

```html
<div class="index-page">
  <div class="index-header">
    <h1>[Project Name]</h1>
    <p>[Design system description] — [N] Screens</p>
    <div class="index-actions">
      <button onclick="toggleDarkMode()">Toggle Dark Mode</button>
      <button onclick="clearAllState(); location.reload();">Reset All Data</button>
      <a href="IMPL-MAPPING.md" target="_blank">View Implementation Mapping</a>
    </div>
  </div>

  <!-- One section per flow -->
  <div class="index-section">
    <h2>Auth Flow</h2>
    <div class="index-links">
      <a href="auth-splash.html" class="index-link">Splash Screen</a>
      <a href="auth-phone.html" class="index-link">Phone Entry</a>
      <a href="auth-otp.html" class="index-link">OTP Verification</a>
    </div>
  </div>

  <div class="index-section">
    <h2>Main Screens</h2>
    <div class="index-links">
      <a href="main-home.html" class="index-link">Home</a>
      <!-- ... -->
    </div>
  </div>

  <!-- Sections for: Onboarding, Main, Detail, Features, Settings, Modals, etc. -->
</div>
```

---

## STEP 5: Create Implementation Mapping Doc

Generate `IMPL-MAPPING.md` — a reference that maps every CSS class, design token, and component to its target platform equivalent. This is what Stage 7 (Implementation) uses to build the real app.

### For Android (Jetpack Compose):

```markdown
# CSS → Jetpack Compose Mapping Reference

## Color Tokens
| CSS Variable | Light Value | Dark Value | Compose Property |
|---|---|---|---|
| `--primary` | `#2563eb` | `#93B8FF` | `MaterialTheme.colorScheme.primary` |

## Spacing Tokens
| CSS Variable | Value | Compose |
|---|---|---|
| `--sp-md` | `16px` | `16.dp` |

## Component Mapping
| CSS Class | Compose Implementation |
|---|---|
| `.card-elevated` | `ElevatedCard(elevation = CardDefaults.elevatedCardElevation(4.dp))` |
| `.btn-filled` | `Button(onClick, shape = CircleShape) { Text(...) }` |
| `.bottom-nav` | `NavigationBar { NavigationBarItem(...) }` |

## Animation Mapping
| CSS Animation | Compose Equivalent |
|---|---|
| `fadeInUp 300ms` | `fadeIn(tween(300)) + slideInVertically(initialOffsetY = { 12 })` |
```

### For iOS (SwiftUI):

Map to SwiftUI equivalents: `Color.accentColor`, `RoundedRectangle`, `NavigationStack`, etc.

### For React/Web:

Map to component library equivalents (MUI, shadcn/ui, Tailwind classes, etc.).

---

## STEP 6: Apply Nielsen's 10 Heuristics

After generating all screens, validate the complete prototype against all 10 heuristics. Fix violations before delivering.

| # | Heuristic | Validation Check | Fix If Missing |
|---|-----------|-----------------|----------------|
| 1 | Visibility of system status | Loading states, active nav indicators, progress feedback | Add spinners, progress bars, active states |
| 2 | Match between system and real world | Labels use user language, familiar icons | Rewrite labels, use standard iconography |
| 3 | User control and freedom | Back buttons, cancel actions, undo for destructive ops | Add cancel/back on every modal and form |
| 4 | Consistency and standards | Same styles across all screens, consistent nav position | Enforce shared.css tokens throughout |
| 5 | Error prevention | Required field markers, confirmation dialogs | Add `required`, confirm modals |
| 6 | Recognition rather than recall | Visible labels (not placeholders), breadcrumbs | Replace placeholder-only inputs with labels |
| 7 | Flexibility and efficiency | Keyboard nav, logical tab order | Add `tabindex` where useful |
| 8 | Aesthetic and minimalist design | Clear visual hierarchy, whitespace | Remove clutter, increase spacing |
| 9 | Help users recognize errors | Inline validation, descriptive error text | Add error messages |
| 10 | Help and documentation | Tooltips on complex fields | Add `title` attributes, help icons |

---

## STEP 7: Add PRD Traceability Annotations

Tag every interactive element with `data-req` attributes linking back to PRD acceptance criteria:

```html
<form data-req="AC-001" data-req-title="User can log in with phone and OTP">
  <input type="tel" data-req="AC-001.1" required>
  <button type="submit" data-req="AC-001.2">Send OTP</button>
</form>
```

Add a traceability overlay toggle in `shared.js` (activated via `?trace=show` query param):

```javascript
function toggleTraceability() {
  document.querySelectorAll('[data-req]').forEach(el => {
    el.classList.toggle('trace-highlight');
    // Show data-req value as a colored overlay badge
  });
}
```

---

## STEP 8: Walkthrough Summary

After generating the complete prototype, present a structured walkthrough:

```markdown
## Prototype Walkthrough

**Directory:** `docs/ui-prototype/` (or `demos/`)
**Total screens:** <N> HTML files
**Shared files:** shared.css, shared.js, IMPL-MAPPING.md
**Requirements covered:** <N> / <total> acceptance criteria

### Flow Summary

| Flow | Screens | Files |
|------|---------|-------|
| Auth | Splash → Phone → OTP | 3 |
| Onboarding | Steps 1-5 → Generation | 6 |
| Main | Home, Chat, Favorites, Stats | 4 |
| Settings | Main + 10 sub-screens | 11 |
| Modals | Sheets, dialogs, confirmations | 12 |

### How to Demo

1. Open `index.html` in any modern browser
2. Click any screen link to navigate to it
3. Use in-screen links/buttons to navigate between screens
4. Append `?trace=show` to any URL to see requirement annotations
5. Use "Toggle Dark Mode" on the index page to switch themes
6. Use "Reset All Data" to clear all localStorage state

### Requirements Not Yet Covered

| Requirement | Reason | Recommendation |
|-------------|--------|---------------|
| AC-050 | Requires real-time API | Simulate with mock data in next iteration |
```

---

## MUST DO

- Generate one HTML file per screen — NOT a single monolithic file
- Create `shared.css` and `shared.js` as the shared design system
- Create `index.html` as the master screen map with all flows organized
- Create `IMPL-MAPPING.md` mapping CSS to target platform (Compose, SwiftUI, React, etc.)
- Use `<a href>` links for navigation between screens (NOT JS routing)
- Use `localStorage` via shared helpers for cross-screen state persistence
- Use realistic, domain-appropriate mock data (NOT lorem ipsum)
- Support both light and dark themes via CSS custom properties
- Validate against Nielsen's 10 heuristics after generation
- Add `data-req` attributes for PRD traceability
- Use semantic HTML elements (`<nav>`, `<main>`, `<section>`, `<form>`, `<button>`)
- Ensure touch targets are at least 44x44px
- Name files with flow prefixes (`auth-`, `main-`, `settings-`, `modal-`, etc.)

## MUST NOT DO

- MUST NOT cram all screens into a single HTML file — use one file per screen
- MUST NOT use external CSS/JS frameworks (CDN fonts are the only exception)
- MUST NOT use JS-based SPA routing — use real `<a href>` links between files
- MUST NOT use placeholder-only form inputs — always pair with visible `<label>` elements
- MUST NOT include real data, credentials, or API keys in prototype content
- MUST NOT use fixed pixel widths that break on mobile viewports
- MUST NOT skip the implementation mapping doc — it's what makes the prototype useful for Stage 7
- MUST NOT generate screens that are not traceable to at least one PRD requirement
