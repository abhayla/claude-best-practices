# Baseline Directory Structure

### Baseline Directory Structure

```
e2e/maestro/
  baselines/        # Committed to version control
    auth/
      login-complete.png
      signup-success.png
    home/
      home-feed.png
      search-results.png
  current/          # Generated during test run (gitignored)
    auth/
      login-complete.png
    home/
      home-feed.png
  diffs/            # Side-by-side comparison images (gitignored)
    home/
      home-feed-diff.png
```

Add to `.gitignore`:
```
e2e/maestro/current/
e2e/maestro/diffs/
```

