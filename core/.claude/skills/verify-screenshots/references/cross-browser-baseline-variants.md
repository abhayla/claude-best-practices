# CROSS-BROWSER BASELINE VARIANTS

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

