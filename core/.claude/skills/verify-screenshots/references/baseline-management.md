# BASELINE MANAGEMENT

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

