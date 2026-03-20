# ANTI-FLAKE CHECKLIST

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

