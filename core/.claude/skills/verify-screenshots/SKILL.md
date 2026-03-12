---
name: verify-screenshots
description: >
  Visual regression testing and screenshot verification. Validates files, uses multimodal
  Read for content analysis, compares against baselines, manages baseline storage,
  integrates with CI for automated visual diff reporting. Use for one-off verification
  or full visual regression pipelines.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<screenshot-path or directory> [--update-baselines] [--strict] [--threshold=N]"
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
