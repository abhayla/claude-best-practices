# CONFIGURABLE THRESHOLDS

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

