# CI INTEGRATION

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

