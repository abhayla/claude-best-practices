---
name: verify-screenshots
description: >
  Validate screenshots against baselines using multimodal content analysis for visual
  regression testing. Manages baseline storage and integrates with CI for automated
  visual diff reporting. Use when running one-off screenshot verification or full
  visual regression pipelines.
  NOT for running full E2E suites with visual verification (use /e2e-visual-run),
  cross-platform visual parity (use /cross-platform-visual), or pipeline-integrated
  visual review as part of auto-verify (invoked automatically by /auto-verify Step 2.5).
triggers:
  - verify screenshot
  - visual regression test
  - screenshot baseline comparison
  - update visual baselines
  - screenshot diff check
  - visual proof verification
allowed-tools: "Bash Read Write Grep Glob"
argument-hint: "<screenshot-path or directory> [--update-baselines] [--strict] [--threshold=N] [--proof-mode --run-id=<id>]"
version: "2.2.0"
type: workflow
---

**Preamble:** Strategy priority is ALWAYS baseline > text hint > generic AI — MUST NOT skip a higher-priority strategy. MUST NOT update baselines without visual review. When invoked by tester-agent, return a single PASSED/FAILED verdict — not a full report. If $ARGUMENTS is empty and --proof-mode is not set, error with usage instructions.

# Verify Screenshots — Visual Regression Testing

Validate screenshot files, compare against baselines, and manage visual regression testing end-to-end.

**Target:** $ARGUMENTS

If `$ARGUMENTS` is empty or contains only flags (no path and no `--proof-mode`):
1. Check for `--proof-mode` flag → proceed to Step 0.5
2. Otherwise: error "No screenshot path provided. Usage: `/verify-screenshots <path> [--update-baselines] [--proof-mode --run-id=<id>]`"

---

## STEP 0.5: Proof Mode (if --proof-mode)

When invoked with `--proof-mode`, read screenshots from the evidence archive
instead of from manually specified paths:

1. Read `test-evidence/{run_id}/manifest.json`
2. For each entry in `screenshots[]`:
   - Set the target path to `test-evidence/{run_id}/{entry.screenshot}`
   - Tag with the test result (`entry.result`) for review context
3. Proceed to STEP 1 (File Validation) with the manifest-derived paths

If `--run-id` is not provided, find the most recent `test-evidence/*/manifest.json`
by timestamp.

This mode is used by `/auto-verify` Step 2.5 for pipeline-integrated visual review,
but can also be invoked standalone to review evidence from a previous run:

```bash
/verify-screenshots --proof-mode --run-id=2026-03-17T14:30:00Z_abc1234
```

## STEP 1: File Validation

Verify the target screenshots exist and are valid:

```bash
ls -la $TARGET_PATH
file $TARGET_PATH  # Check file type
```

Ensure files are:
- Non-zero size
- Valid image format (PNG, JPG, etc.)
- Recently created/modified

## STEP 1.5: Verification Strategy Selection

For each screenshot, determine the verification strategy in priority order:

```
For each screenshot:
  1. Check for baseline at baselines/{test_name}.png
     → If exists: use BASELINE COMPARISON (pixel/AI diff — see Step 3)
  2. Check for text hint:
     a. In manifest entry: screenshots[].visual_expectation field
     b. In visual-tests.yml: expectations.{test_name}.description
     → If exists: use TEXT-HINT AI REVIEW (see Step 2, text-hint mode)
  3. If neither baseline nor text hint exists:
     → Use GENERIC AI REVIEW (see Step 2, generic mode)
```

| Strategy | Precision | Setup Required | Best For |
|----------|-----------|----------------|----------|
| Baseline comparison | Highest — pixel-level or AI semantic diff | Baseline screenshots must be committed | Stable UI, design system components |
| Text-hint AI review | High — verifies specific expected elements | One-line description per test | Dynamic pages, data-driven screens |
| Generic AI review | Medium — catches obvious failures only | None | First-run, prototype, exploratory tests |

### visual-tests.yml Expectations Format

Projects can define per-test visual expectations in `visual-tests.yml`:

```yaml
# visual-tests.yml (optional — placed in project root)
expectations:
  test_login_page:
    description: "Login form with email and password fields, submit button enabled"
  test_dashboard:
    description: "3 chart widgets populated with data, sidebar navigation visible"
  test_checkout_flow:
    description: "Order summary with item list, total price, and payment button"

# Override UI test detection (optional)
ui_test_patterns:
  include: ["tests/e2e/**", "tests/visual/**"]
  exclude: ["tests/e2e/api_only/**"]
```

### Per-Test Verdict Return (when invoked by tester-agent)

When this skill is invoked by `tester-agent` for per-test screenshot verification
(not batch mode), return a single structured verdict:

```json
{
  "test": "test_name",
  "verdict": "PASSED|FAILED",
  "confidence": "HIGH|MEDIUM|LOW",
  "strategy": "baseline|text_hint|generic_ai",
  "reason": "One-line explanation of verdict"
}
```

Confidence levels:
- **HIGH** — baseline match within threshold, or AI review with clear pass/fail signals
- **MEDIUM** — AI review with some ambiguity (e.g., partial data load, borderline layout)
- **LOW** — generic AI review with no baseline or text hint to compare against

## STEP 2: Content Analysis

Use multimodal Read to analyze each screenshot:

1. Read the image file to view its contents
2. **If text hint available (from Step 1.5):** Verify the screenshot matches the
   specific description. Check each element mentioned in the hint is present
   and correctly rendered. Report which elements match and which are missing.
3. **If no text hint (generic mode):** Check for:
   - Expected UI elements are visible
   - No error dialogs or crash screens
   - Text is readable and not truncated
   - Layout appears correct (no overlapping elements)
   - Loading states are resolved (no spinners in final screenshots)
   - Data containers are populated (tables have rows, lists have items, charts have data points)
   - No empty-state placeholders visible when data is expected (e.g., "No results found" when results should exist)
   - Dynamic content regions contain actual content, not just structural chrome
   - Timestamps or dates visible in the UI are within expected recency (not showing yesterday's date for live data)

### Data Presence vs Visual Correctness

Visual regression catches layout/style changes but misses empty or stale data. When verifying screenshots of data-driven screens, check BOTH:

| Check Type | What It Catches | How |
|-----------|----------------|-----|
| **Visual correctness** | Layout shifts, missing elements, style regressions | Baseline comparison (pixel diff or AI diff) |
| **Data presence** | Empty tables, blank charts, missing list items | Multimodal Read: count visible data rows, verify content regions are populated |
| **Data freshness** | Stale/cached data, yesterday's timestamps | Read timestamps in screenshot, verify recency |
| **Data validity** | Garbled text, NaN values, placeholder text ("Lorem ipsum", "undefined") | Read text content, check for known placeholder patterns |

When using multimodal Read to verify a screenshot, always answer these questions:
1. **Is there data?** — Are data containers (tables, lists, cards, charts) populated with at least one item?
2. **Is the data real?** — Does the content look like real data (not placeholder/test data like "Lorem ipsum", "test123", "undefined", "null", "NaN")?
3. **Is the data current?** — If timestamps are visible, are they recent (within expected update interval)?
4. **Is the data complete?** — Are all expected sections populated, or are some showing empty/loading states?

## STEP 3: Before/After Comparison (if applicable)

If both before and after screenshots are provided:

1. Read both images
2. Compare:
   - What changed between them
   - Whether the change matches expectations
   - No unintended side effects visible

## STEP 4: Report

```
Screenshot Verification:
  Files checked: N
  Valid: Y
  Issues found: Z

  Per-file results:
  - [filename]: PASS — [brief description of content]
  - [filename]: FAIL — [issue description]
```

---

## BASELINE MANAGEMENT


**Read:** `references/baseline-management.md` for detailed baseline management reference material.

## CONFIGURABLE THRESHOLDS


**Read:** `references/configurable-thresholds.md` for detailed configurable thresholds reference material.

## CROSS-BROWSER BASELINE VARIANTS


**Read:** `references/cross-browser-baseline-variants.md` for detailed cross-browser baseline variants reference material.

## CI INTEGRATION


**Read:** `references/ci-integration.md` for detailed ci integration reference material.

## AI VISUAL DIFF vs PIXEL DIFF

### When to Use Each

| Approach | Use When | Tools | False Positive Rate |
|----------|----------|-------|-------------------|
| **Pixel diff** | Design system components, icons, pixel-perfect layouts | Playwright `toHaveScreenshot`, BackstopJS, Lost Pixel | Higher — flags anti-aliasing, font rendering |
| **AI visual diff** | Full pages with dynamic content, cross-browser testing | Applitools Eyes, Percy, Functionize | Lower — understands semantic changes |
| **LLM multimodal** | Design review, regression triage, complex layouts | Claude Read, GPT-4V | Lowest — but slower and non-deterministic |
| **Hybrid** | Component=pixel-strict, Page=AI-tolerant | Mix per test type | Optimal balance |

### Key Difference

Pixel diff: "N pixels changed" → flags anti-aliasing as regression.
AI visual diff: "Button moved 2px" → ignore. "Button disappeared" → fail.

### Integration Pattern

```json
{
  "comparisonStrategy": {
    "designSystemComponents": "pixel-diff",
    "fullPages": "ai-visual-diff",
    "designReview": "llm-multimodal"
  },
  "tools": {
    "pixel": { "tool": "playwright", "threshold": 0.1 },
    "ai": { "service": "percy", "sensitivity": "medium" },
    "llm": { "model": "claude", "prompt": "classify-change" }
  }
}
```

### Self-Hosted Alternatives

For teams that cannot use cloud visual testing services:

| Tool | Type | How It Works |
|------|------|-------------|
| **Lost Pixel** | Open-source | Storybook/Ladle/page screenshots, GitHub Actions native, baseline in repo |
| **BackstopJS** | Open-source | Puppeteer + ResembleJS, JSON config, viewport arrays, CI integration |
| **reg-suit** | Open-source | S3/GCS baseline storage, PR comment reports |

---

## LLM-ASSISTED VISUAL TRIAGE

When pixel diff or AI diff flags a change, use multimodal LLM to classify and triage:

### Triage Workflow

1. Collect three images: `baseline.png`, `current.png`, `diff.png`
2. Read all three images using multimodal Read
3. Classify the change:

| Classification | Description | Action |
|---------------|-------------|--------|
| `INTENTIONAL_REDESIGN` | Deliberate layout/style change matching recent commits | Route to design review → update baseline |
| `REGRESSION` | Unintended visual break (missing element, broken layout) | Flag for immediate fix → suggest CSS/code fix |
| `RENDERING_VARIANCE` | Anti-aliasing, font rendering, sub-pixel noise | Auto-approve → increase threshold for this element |
| `DYNAMIC_CONTENT` | Timestamps, ads, user-specific data leaked through mask | Auto-approve → add mask for this region |

### Automated Triage Prompt

When triaging a visual diff, analyze the three screenshots with this framework:

1. **What changed?** — Identify specific elements that differ
2. **Is it structural?** — Layout shift, missing/added element, size change = likely REGRESSION
3. **Is it cosmetic?** — Color shift, font rendering, shadow difference = likely RENDERING_VARIANCE
4. **Is it content?** — Different text, numbers, dates = likely DYNAMIC_CONTENT
5. **Does it match recent code changes?** — Check git diff for related CSS/component changes = likely INTENTIONAL_REDESIGN

### Auto-Resolution Rules

- `RENDERING_VARIANCE` with <2% pixel diff → auto-approve, no action needed
- `DYNAMIC_CONTENT` → auto-approve, add mask configuration for the region
- `REGRESSION` → block PR, create issue with fix suggestion
- `INTENTIONAL_REDESIGN` → require explicit baseline update commit

---

## ANTI-FLAKE CHECKLIST

Eliminate false positives from visual tests with these deterministic rendering techniques:


**Read:** `references/anti-flake-checklist.md` for detailed anti-flake checklist reference material.

## DESIGN-TO-CODE VALIDATION

Compare implemented UI against original design files (Figma, Sketch) to catch design drift.

### Workflow

1. **Export design frames** — Export target screens from Figma as PNG at 1x resolution
2. **Capture implementation** — Screenshot the running application at matching viewport
3. **Compare** — Use AI visual diff or LLM multimodal comparison (pixel diff too strict for design-to-code)
4. **Report deviations** — Flag spacing, color, typography, and component differences

### Figma Export Automation

```bash
# Export Figma frames via API (requires access token)
curl -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_IDS&format=png&scale=1" \
  | jq -r '.images | to_entries[] | .value' \
  | xargs -I {} curl -o "designs/{}.png" {}
```

### Comparison Criteria

| Criterion | Tolerance | Notes |
|-----------|-----------|-------|
| Layout structure | Strict | Elements must match grid/flex layout |
| Colors | ±5 RGB values | Account for color profile differences |
| Typography | Font size ±1px, weight exact | Font family may differ (system vs web) |
| Spacing | ±4px | Sub-pixel rendering causes minor variance |
| Border radius | ±2px | Platform rendering differences |
| Shadows | Tolerant | Shadow rendering varies significantly across renderers |

### When to Run

- On every PR that touches UI components
- Weekly scheduled comparison for design drift detection
- After design system updates

---

## COMPONENT-LEVEL VISUAL TESTING

Full-page screenshots miss regressions inside individual components. Component-level testing captures each component state in isolation.

### Why Component-Level Over Full-Page

| Approach | Catches | Misses |
|----------|---------|--------|
| Full-page screenshot | Layout shifts, missing sections | Broken button states, theme issues inside components |
| Component screenshot | Every state (hover, disabled, loading, error), every theme | Full-page layout integration |
| Both (recommended) | Everything | — |

### Storybook + Chromatic (Cloud)

```javascript
// Write stories for every meaningful state
// Button.stories.tsx
export default { title: 'Components/Button', component: Button };

export const Default = { args: { label: 'Submit' } };
export const Disabled = { args: { label: 'Submit', disabled: true } };
export const Loading = { args: { label: 'Submit', loading: true } };
export const Error = { args: { label: 'Retry', variant: 'error' } };

// Each story automatically becomes a visual test in Chromatic
// No test code needed — just write stories
```

```bash
# Run visual tests via Chromatic (cloud)
npx chromatic --project-token=$CHROMATIC_TOKEN

# TurboSnap: only re-snapshot stories whose dependencies changed
npx chromatic --project-token=$CHROMATIC_TOKEN --only-changed
# Reduces CI time by 50-80% on incremental changes
```

### Storybook + Lost Pixel (Self-Hosted)

```javascript
// lostpixel.config.ts (self-hosted alternative to Chromatic)
module.exports = {
  storybookShots: {
    storybookUrl: 'http://localhost:6006',
  },
  generateOnly: true,  // Generate screenshots without cloud upload
  threshold: 0.1,       // 0.1% pixel tolerance
  beforeScreenshot: async (page) => {
    // Disable animations for deterministic captures
    await page.addStyleTag({
      content: '*, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }'
    });
  },
};
```

```bash
# Run Lost Pixel (open-source, self-hosted)
npx lost-pixel

# Update baselines
npx lost-pixel --update
```

### Modes: Combinatorial Coverage

Test the same component across themes, viewports, and locales without creating separate stories:

```javascript
// .storybook/modes.js — define test matrix
export const modes = {
  'light-mobile': { theme: 'light', viewport: { width: 375, height: 812 } },
  'light-desktop': { theme: 'light', viewport: { width: 1440, height: 900 } },
  'dark-mobile': { theme: 'dark', viewport: { width: 375, height: 812 } },
  'dark-desktop': { theme: 'dark', viewport: { width: 1440, height: 900 } },
};
// Each story × each mode = N screenshots automatically
// 10 stories × 4 modes = 40 visual tests from 10 lines of config
```

### Play Functions: Interactive State Capture

```javascript
// Simulate interactions and capture the resulting state
export const FilledForm = {
  args: { /* ... */ },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByLabelText('Email'), 'test@example.com');
    await userEvent.type(canvas.getByLabelText('Password'), 'password123');
    // Visual snapshot captures the filled-form state automatically
  },
};
```

### CI Integration

```yaml
# GitHub Actions
visual-components:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with: { fetch-depth: 0 }  # Needed for TurboSnap
    - run: npm ci
    - run: npx chromatic --project-token=${{ secrets.CHROMATIC_TOKEN }} --only-changed
    # Or self-hosted:
    # - run: npm run build-storybook
    # - run: npx lost-pixel
```

### When to Use Component vs Full-Page Visual Testing

| Use Component Testing For | Use Full-Page Testing For |
|--------------------------|--------------------------|
| Design system components | Page layout integration |
| Interactive states (hover, focus, active) | Navigation flow screenshots |
| Theme variants (light/dark) | Full user journey captures |
| Responsive breakpoints per component | Cross-page consistency |
| Form validation states | E2E visual regression |

---

## CRITICAL RULES

### MUST DO
- MUST validate file existence before attempting to read — Why: multimodal Read on missing files produces confusing errors
- MUST report specific issues per file, not just aggregate pass/fail — Why: reviewers need to know exactly which screenshot failed and why
- MUST flag screenshots showing error dialogs or crash screens as CRITICAL — Why: these indicate app-level failures, not visual regressions
- MUST follow strategy priority: baseline > text hint > generic AI — Why: higher-priority strategies have higher precision; skipping them produces false passes
- MUST check every element in text-hint descriptions — Why: partial matches mask missing elements; list what was found and what was missing
- MUST read both baseline and current images before approving baseline updates — Why: blind baseline updates can bake in regressions
- MUST log corrupt/unreadable images as SKIPPED with reason, not FAILED — Why: corrupt files are infrastructure issues, not visual regressions

### MUST NOT DO
- MUST NOT update baselines without visual review — Why: auto-approving baseline updates defeats the purpose of visual testing
- MUST NOT silently pass when baselines are missing — flag as "needs baseline" instead — Why: missing baselines mean no regression protection
- MUST NOT produce a full report when invoked by tester-agent for per-test verdict — return single PASSED/FAILED with confidence and one-line reason instead — Why: tester-agent expects structured verdict, not prose
- MUST NOT disable visual tests because of dynamic content — use masks instead — Why: disabling tests creates blind spots; masks preserve coverage while tolerating expected variance
