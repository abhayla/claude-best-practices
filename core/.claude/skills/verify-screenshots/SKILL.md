---
name: verify-screenshots
description: >
  Visual regression testing and screenshot verification. Validates files, uses multimodal
  Read for content analysis, compares against baselines, manages baseline storage,
  integrates with CI for automated visual diff reporting. Use for one-off verification
  or full visual regression pipelines.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<screenshot-path or directory> [--update-baselines] [--strict] [--threshold=N]"
version: "1.0.0"
type: workflow
---

# Verify Screenshots — Visual Regression Testing

Validate screenshot files, compare against baselines, and manage visual regression testing end-to-end.

**Target:** $ARGUMENTS

---

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

## STEP 2: Content Analysis

Use multimodal Read to analyze each screenshot:

1. Read the image file to view its contents
2. Check for:
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

### Directory Structure

Store baselines alongside tests using a predictable directory layout:

```
project-root/
  tests/
    visual/
      baselines/                    # Committed to version control
        chrome-linux/               # Platform variant (see Cross-Browser section)
          homepage.png
          dashboard.png
        firefox-linux/
          homepage.png
          dashboard.png
      current/                      # Generated during test run (gitignored)
        homepage.png
        dashboard.png
      diffs/                        # Generated diff images (gitignored)
        homepage-diff.png
      visual.config.json            # Threshold and mask configuration
```

Add to `.gitignore`:

```
tests/visual/current/
tests/visual/diffs/
```

### Storing and Versioning Baselines

- Baselines in `baselines/` MUST be committed to version control. They are the source of truth.
- Use LFS (`git lfs track "tests/visual/baselines/**/*.png"`) for repos with many or large baseline images. This prevents binary bloat in git history.
- Name baselines after the component or page they represent: `login-form.png`, `navbar-collapsed.png`. Avoid generic names like `test1.png`.

### Updating Baselines

When a visual change is intentional, update baselines explicitly:

1. **Run tests to generate current screenshots** into `tests/visual/current/`.
2. **Review diffs visually** — read both the baseline and current image, confirm the change is intentional.
3. **Copy approved screenshots** from `current/` to `baselines/`:
   ```bash
   cp tests/visual/current/homepage.png tests/visual/baselines/chrome-linux/homepage.png
   ```
4. **Commit updated baselines** in a dedicated commit with a message explaining what changed and why:
   ```
   chore(visual): update homepage baseline — new hero banner layout
   ```

### Approval Workflow

For team environments, use this workflow before merging baseline updates:

1. The PR that changes baselines MUST include before/after images in the PR description or as CI artifacts.
2. At least one reviewer MUST confirm the visual change is intentional by viewing the diff images.
3. Never batch unrelated baseline updates — each PR should update baselines for a single feature or fix.
4. If `--update-baselines` is passed as an argument, automate the copy step but still require manual review before commit.

---

## CONFIGURABLE THRESHOLDS

### Configuration File

Create `tests/visual/visual.config.json` to control comparison behavior:

```json
{
  "defaultThreshold": 0.1,
  "strict": false,
  "antiAliasingTolerance": 2,
  "perElement": {},
  "masks": [],
  "fullPage": {
    "threshold": 0.5
  }
}
```

### Threshold Modes

| Mode | Threshold | Use Case |
|------|-----------|----------|
| **Strict** | `0.0` (0% tolerance) | Pixel-perfect layouts, design system components, icons |
| **Standard** | `0.1` (allow 0.1% pixel diff) | General UI pages — absorbs sub-pixel rendering variance |
| **Tolerant** | `0.5` (allow 0.5% pixel diff) | Pages with minor anti-aliasing differences across runs |
| **Loose** | `2.0`+ | Smoke-test level — catches major regressions only |

### Per-Element vs Full-Page Thresholds

Apply different thresholds to different components:

```json
{
  "defaultThreshold": 0.1,
  "perElement": {
    "header-nav": 0.0,
    "hero-banner": 0.5,
    "footer": 1.0
  },
  "fullPage": {
    "threshold": 0.5
  }
}
```

- **Per-element**: Crop or isolate a component screenshot. Use strict thresholds for critical UI (navigation, forms). Use tolerant thresholds for content-heavy areas.
- **Full-page**: Higher threshold to accommodate cumulative minor differences across the whole page.

### Masking Dynamic Content

Mask regions that change between runs to prevent false positives:

```json
{
  "masks": [
    { "name": "timestamp", "selector": "[data-testid='timestamp']", "region": { "x": 10, "y": 50, "width": 200, "height": 30 } },
    { "name": "avatar", "selector": ".user-avatar", "region": { "x": 400, "y": 10, "width": 48, "height": 48 } },
    { "name": "ads", "selector": ".ad-banner", "region": { "x": 0, "y": 600, "width": 728, "height": 90 } },
    { "name": "animation", "selector": ".loading-shimmer" }
  ]
}
```

Common items to mask:
- Timestamps and relative dates ("3 minutes ago")
- User avatars and profile images
- Ad banners and third-party embeds
- Animated elements (carousels, shimmers)
- Randomly generated content (A/B test variants)

When using `selector`-based masks, the test runner should hide the element before capture. When using `region`-based masks, the comparison tool should ignore those pixel coordinates.

### Applying Thresholds at Runtime

If `--strict` is passed, override all thresholds to `0.0`. If `--threshold=N` is passed, override the default threshold to `N`. Per-element overrides still apply unless `--strict` is used.

---

## CROSS-BROWSER BASELINE VARIANTS

### Separate Baselines Per Platform

Different browsers and operating systems render fonts, anti-aliasing, and sub-pixel layouts differently. Maintain separate baselines per platform:

```
baselines/
  chrome-linux/
  chrome-macos/
  chrome-windows/
  firefox-linux/
  firefox-macos/
  safari-macos/
  mobile-chrome-android/
  mobile-safari-ios/
```

### Naming Convention

Use the format `{browser}-{os}` for baseline directories. The test runner detects the current platform and selects the matching baseline directory automatically.

### Managing Baseline Explosion

As browsers and viewports multiply, the number of baseline images grows rapidly. Mitigate with these strategies:

1. **Tier your browsers**: Only maintain strict baselines for primary browsers (e.g., `chrome-linux`). Use tolerant thresholds for secondary browsers instead of separate baselines.
2. **Share baselines where possible**: If Chrome on Linux and Chrome on Windows produce identical output for a component, symlink or share the baseline. Only create platform-specific baselines when rendering actually differs.
3. **Viewport buckets**: Use 3 standard viewports (mobile: 375px, tablet: 768px, desktop: 1440px) rather than testing every breakpoint.
4. **Component-level over full-page**: Test individual components rather than full pages — components are more consistent across browsers and require fewer baselines.
5. **Periodic pruning**: Quarterly, audit baselines for dropped browser support or unused viewports. Remove stale platform directories.

### Platform-Specific Rendering Differences

Common differences to expect and account for:

| Difference | Affected Browsers | Mitigation |
|------------|-------------------|------------|
| Font rendering / hinting | All (varies by OS) | Use tolerant threshold or separate baselines |
| Sub-pixel anti-aliasing | Safari vs Chrome | Set `antiAliasingTolerance: 2` or higher |
| Scrollbar width | Windows vs macOS/Linux | Use `overflow: overlay` or mask scrollbar region |
| Form control styling | Firefox vs Chrome vs Safari | Use custom-styled controls or mask native inputs |
| Emoji rendering | All (varies by OS version) | Mask emoji regions or use image fallbacks |

---

## CI INTEGRATION

### Running Visual Tests in CI

Add a visual regression step to your CI pipeline. Example GitHub Actions workflow:

```yaml
name: Visual Regression
on: [pull_request]

jobs:
  visual-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # Pull baseline images from LFS

      - name: Install dependencies
        run: npm ci

      - name: Run visual regression tests
        run: npm run test:visual
        env:
          VISUAL_PLATFORM: chrome-linux

      - name: Upload diff artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-diffs
          path: tests/visual/diffs/
          retention-days: 14

      - name: Upload current screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-current
          path: tests/visual/current/
          retention-days: 14
```

### Posting Visual Diffs as PR Comments

When visual tests fail, post diff images directly on the PR for easy review:

```yaml
      - name: Comment visual diffs on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const path = require('path');
            const diffDir = 'tests/visual/diffs';
            if (!fs.existsSync(diffDir)) return;

            const diffs = fs.readdirSync(diffDir).filter(f => f.endsWith('.png'));
            if (diffs.length === 0) return;

            let body = '## Visual Regression Detected\n\n';
            body += `**${diffs.length} screenshot(s)** differ from baselines.\n\n`;
            body += 'Download the `visual-diffs` and `visual-current` artifacts to review.\n\n';
            body += '| Screenshot | Status |\n|---|---|\n';
            for (const diff of diffs) {
              const name = diff.replace('-diff.png', '');
              body += `| \`${name}\` | Changed |\n`;
            }
            body += '\n\nIf these changes are intentional, update baselines:\n';
            body += '```bash\nnpm run test:visual -- --update-baselines\ngit add tests/visual/baselines/\n```';

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body
            });
```

### Pass/Fail Thresholds in CI

Control how visual test results affect the build:

```json
{
  "ci": {
    "failOnAnyDiff": false,
    "maxAllowedDiffs": 0,
    "failOnMissingBaseline": true,
    "requireBaselineApproval": true
  }
}
```

| Setting | Value | Effect |
|---------|-------|--------|
| `failOnAnyDiff` | `true` | Any pixel difference fails the build (strict mode) |
| `failOnAnyDiff` | `false` | Applies threshold-based comparison |
| `maxAllowedDiffs` | `0` | Zero screenshots may exceed their threshold |
| `maxAllowedDiffs` | `3` | Up to 3 screenshots may exceed threshold before failing |
| `failOnMissingBaseline` | `true` | New screenshots without baselines fail the build |
| `requireBaselineApproval` | `true` | Baseline updates require reviewer approval on the PR |

### Artifact Upload for Review

Always upload these artifacts on failure so reviewers can inspect without re-running the pipeline:

1. **`visual-diffs/`** — Side-by-side or overlay diff images highlighting changed pixels.
2. **`visual-current/`** — The actual screenshots from this run.
3. **`visual-baselines/`** — (Optional) The baseline images for comparison. Only upload if baselines are not easily accessible from the repo.

Set `retention-days` to 14 (or your team's review SLA) to avoid unbounded storage growth.

---

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

### Before Capture

```javascript
// Inject CSS to disable ALL animations before screenshot
await page.addStyleTag({
  content: `
    *, *::before, *::after {
      animation-duration: 0s !important;
      animation-delay: 0s !important;
      transition-duration: 0s !important;
      transition-delay: 0s !important;
      caret-color: transparent !important;
    }
  `
});

// Wait for network idle (no pending requests)
await page.waitForLoadState('networkidle');

// Wait for all fonts to load
await page.evaluate(() => document.fonts.ready);

// Force consistent device scale factor
// Launch with: --force-device-scale-factor=1

// Set deterministic viewport, timezone, locale, color scheme
await page.setViewportSize({ width: 1440, height: 900 });
```

### Environment Normalization

| Technique | Why | How |
|-----------|-----|-----|
| **Docker container** | Eliminates OS-level rendering differences | `mcr.microsoft.com/playwright:v1.x-jammy` |
| **Web fonts only** | System fonts render differently across OS | Self-host fonts or use Google Fonts CDN |
| **Pin browser version** | Browser updates change rendering | Lock version in CI config |
| **Force device scale** | HiDPI/Retina causes pixel density differences | `--force-device-scale-factor=1` |
| **Disable animations** | Animations captured mid-frame cause flakes | CSS injection before capture |
| **Freeze clock** | Timestamps change every run | `page.clock.setFixedTime()` |
| **Deterministic locale** | Number/date formatting varies | Set `locale: 'en-US'` in browser context |

### Checklist

```
Before capture:
  [ ] Animations disabled (CSS injection)
  [ ] Network idle (no pending requests)
  [ ] Fonts loaded (document.fonts.ready)
  [ ] Dynamic content masked (timestamps, avatars, ads)
  [ ] Device scale factor forced to 1
  [ ] Viewport, timezone, locale, color scheme set

Environment:
  [ ] Running in Docker container (deterministic rendering)
  [ ] Browser version pinned in CI
  [ ] Web fonts used (not system fonts)

After capture:
  [ ] Anti-aliasing tolerance applied (2-4px)
  [ ] Percentage threshold for responsive layouts
  [ ] Pixel threshold for small precision components
```

---

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

## RULES

- Always validate file existence before attempting to read
- Report specific issues, not just pass/fail
- If screenshots show errors or crashes, flag as critical
- Compare against expected state if provided in arguments
- Never update baselines without visual review — always read both images before approving
- Commit baseline updates in dedicated commits, separate from code changes
- Use `--strict` for design system components and pixel-critical UI
- Use masks for dynamic content — never disable visual tests because of timestamps or ads
- In CI, always upload diff artifacts on failure so reviewers can inspect without re-running
- When baselines are missing for a new screenshot, flag it as "needs baseline" rather than silently passing
