---
name: web-quality
description: >
  Run a comprehensive web quality audit covering Core Web Vitals, accessibility (WCAG 2.1 AA),
  SEO, performance budgets, responsive design, and progressive enhancement. Produces actionable
  findings with fix guidance. Inspired by Addy Osmani's web-quality-skills (Google Chrome team).
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<url-or-file-path> [--focus=vitals|a11y|seo|perf|responsive|all]"
version: "1.0.0"
type: workflow
---

# Web Quality Audit

Perform a comprehensive web quality audit on the target.

**Target:** $ARGUMENTS

---

## STEP 1: Identify Audit Scope

1. Determine if the target is a URL, a local file path, or an entire project directory
2. If a project directory, locate HTML entry points (`index.html`, layout templates, page components)
3. Parse the `--focus` flag if provided; default to `all`
4. List all pages/components that will be audited

Available focus areas:
- `vitals` — Core Web Vitals (LCP, INP, CLS)
- `a11y` — Accessibility (WCAG 2.1 AA)
- `seo` — Search engine optimization
- `perf` — Performance budgets and optimization
- `responsive` — Responsive design and mobile-first
- `progressive` — Progressive enhancement
- `all` — Everything (default)

---

## STEP 2: Core Web Vitals Audit

Evaluate the three Core Web Vitals metrics. These are Google's primary signals for page experience ranking.


**Read:** `references/core-web-vitals-audit.md` for detailed step 2: core web vitals audit reference material.

# Lighthouse CLI audit (install: npm i -g lighthouse)
lighthouse <URL> --output=json --output=html --output-path=./lighthouse-report

# Lighthouse with specific categories
lighthouse <URL> --only-categories=performance,accessibility,seo,best-practices

# web-vitals library (add to application code for field data)
# npm install web-vitals
```

```javascript
// Field measurement with web-vitals library
import { onLCP, onINP, onCLS } from 'web-vitals';

onLCP(metric => console.log('LCP:', metric.value, 'ms'));
onINP(metric => console.log('INP:', metric.value, 'ms'));
onCLS(metric => console.log('CLS:', metric.value));
```

**Chrome DevTools**: Performance tab > Record > Interact > Stop. Look for:
- Long Tasks (red corners on task bars)
- Layout Shifts (purple markers in Experience lane)
- LCP marker (green line in Timings lane)

---

## STEP 3: Accessibility Audit (WCAG 2.1 AA)


**Read:** `references/accessibility-audit-wcag-21-aa.md` for detailed step 3: accessibility audit (wcag 2.1 aa) reference material.

## STEP 4: SEO Audit


**Read:** `references/seo-audit.md` for detailed step 4: seo audit reference material.

## STEP 5: Progressive Enhancement

Build web experiences that work for everyone, then enhance for capable browsers.

### 5.1 HTML First

- [ ] Core content is readable with CSS and JS disabled
- [ ] Navigation works without JavaScript (server-rendered links)
- [ ] Forms submit to server-side endpoints (not JS-only)
- [ ] `<noscript>` provides fallback messaging where JS is required
- [ ] Critical content is in the HTML source (not injected by JS)
- [ ] Server-side rendering (SSR) or static site generation (SSG) for content pages

### 5.2 CSS Enhancement

```css
/* Feature queries for progressive CSS */
@supports (display: grid) {
  .layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
}

@supports (backdrop-filter: blur(10px)) {
  .glass { backdrop-filter: blur(10px); background: rgba(255,255,255,0.5); }
}

@supports (container-type: inline-size) {
  .card-container { container-type: inline-size; }
}
```

- [ ] `@supports` queries used for newer CSS features
- [ ] Flexbox fallback for Grid layouts where needed
- [ ] CSS custom properties have fallback values: `color: var(--primary, #0066cc)`
- [ ] No layout-critical styles depend on CSS features below 95% browser support

### 5.3 JavaScript Enhancement

- [ ] Feature detection before use (`if ('IntersectionObserver' in window)`)
- [ ] Polyfills loaded conditionally, not bundled for all users
- [ ] Core functionality works with JavaScript errors (graceful degradation)
- [ ] `type="module"` scripts have `nomodule` fallback where needed
- [ ] Service worker registration is wrapped in feature detection

---

## STEP 6: Responsive Design Audit


**Read:** `references/responsive-design-audit.md` for detailed step 6: responsive design audit reference material.

## STEP 7: Performance Budget Audit

### 7.1 Bundle Size Limits

| Resource | Budget (gzipped) | Check Command |
|----------|-----------------|---------------|
| Main JS bundle | < 200KB | `du -sh dist/main.*.js.gz` |
| Total JS | < 400KB | Sum all JS bundles |
| Main CSS | < 50KB | `du -sh dist/main.*.css.gz` |
| Total CSS | < 75KB | Sum all CSS |
| HTML document | < 100KB | Check document size |
| Any single image | < 200KB | Check largest image |
| Total page weight | < 2MB | Check all resources |

```bash
# Analyze bundle with source-map-explorer or webpack-bundle-analyzer
npx source-map-explorer dist/main.*.js
npx webpack-bundle-analyzer stats.json
```

- [ ] Bundle sizes are within budget
- [ ] Tree-shaking is working (no unused exports in bundle)
- [ ] Code splitting is implemented (route-based or component-based)
- [ ] Dynamic imports used for below-fold and modal content
- [ ] No duplicate dependencies in the bundle

### 7.2 Lighthouse Score Targets

| Category | Target | Minimum |
|----------|--------|---------|
| Performance | > 90 | > 70 |
| Accessibility | > 90 | > 85 |
| Best Practices | > 90 | > 80 |
| SEO | > 90 | > 85 |

### 7.3 Image Optimization

- [ ] All images served in WebP or AVIF format (with fallback)
- [ ] Images are appropriately sized (not serving 4000px wide to a 400px container)
- [ ] Image compression is applied (quality 75-85 for photos, lossless for graphics)
- [ ] SVG used for icons and simple graphics
- [ ] SVGs are optimized (run through SVGO)
- [ ] No images above 200KB after compression
- [ ] CSS `image-rendering` set appropriately for different image types

### 7.4 Font Optimization

- [ ] `font-display: swap` on all `@font-face` declarations
- [ ] Fonts are subsetted to needed Unicode ranges
- [ ] WOFF2 format used (best compression)
- [ ] Critical fonts are preloaded: `<link rel="preload" as="font" type="font/woff2" crossorigin>`
- [ ] Maximum 2-3 font families loaded
- [ ] Variable fonts used where multiple weights are needed (reduces total font files)
- [ ] System font stack used as fallback: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`

### 7.5 Third-Party Script Audit

- [ ] All third-party scripts are inventoried with justification
- [ ] Non-critical third-party scripts use `defer` or `async`
- [ ] Tag managers load asynchronously
- [ ] Third-party impact measured with Lighthouse "Third-party usage" audit
- [ ] Unused third-party scripts removed
- [ ] `<link rel="preconnect">` added for critical third-party origins
- [ ] Consider self-hosting critical third-party resources (fonts, analytics)
- [ ] Facades used for heavy embeds (YouTube, social widgets) — load on interaction

---

## STEP 8: Run the Full Audit

Execute the audit using available tooling.

### 8.1 Automated Scans

```bash
# 1. Lighthouse (performance, a11y, SEO, best practices)
lighthouse <URL> \
  --output=json --output=html \
  --output-path=./reports/lighthouse \
  --chrome-flags="--headless"

# 2. axe accessibility scanner (via CLI)
# npm install -g @axe-core/cli
axe <URL> --save=./reports/axe-results.json

# 3. PageSpeed Insights API (includes field data from CrUX)
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<URL>&strategy=mobile"

# 4. Validate structured data
# Visit: https://search.google.com/test/rich-results?url=<URL>

# 5. HTML validation
# npm install -g html-validate
html-validate "src/**/*.html"

# 6. Check broken links
# npm install -g broken-link-checker
blc <URL> --recursive --ordered
```

### 8.2 Manual Checks

Perform these checks that automated tools miss:

1. **Keyboard-only navigation**: Unplug your mouse, navigate the entire page with Tab, Enter, Escape, Arrow keys
2. **Screen reader walkthrough**: Turn on VoiceOver (macOS) or NVDA (Windows), navigate the page
3. **Responsive spot-check**: Resize browser from 320px to 1920px, watch for layout breaks
4. **Slow network**: Chrome DevTools > Network > Slow 3G, verify the page is usable
5. **Print preview**: Check that pages have a print stylesheet or degrade gracefully
6. **Zoom test**: Zoom to 200%, verify no content is clipped or overlapping
7. **Reduced motion**: Enable `prefers-reduced-motion: reduce` in OS settings, verify animations are suppressed

### 8.3 Code-Level Checks

Search the codebase for common anti-patterns:

```bash
# Images without dimensions
grep -rn '<img' --include="*.html" --include="*.tsx" --include="*.jsx" | grep -v 'width'

# Images without alt text
grep -rn '<img' --include="*.html" --include="*.tsx" --include="*.jsx" | grep -v 'alt='

# div used as button
grep -rn 'onClick' --include="*.tsx" --include="*.jsx" | grep '<div'

# Inline styles (potential CLS issues)
grep -rn 'style={{' --include="*.tsx" --include="*.jsx" | head -20

# Missing font-display
grep -rn '@font-face' --include="*.css" --include="*.scss" | grep -v 'font-display'

# Viewport meta check
grep -rn 'viewport' --include="*.html" | head -5
```

---

## STEP 9: Generate Audit Report

Compile findings into a structured report.

### Report Template

```
# Web Quality Audit Report
Date: [date]
Target: [URL or project path]

## Scores
| Category | Score | Target | Status |
|----------|-------|--------|--------|
| Performance (Lighthouse) | XX | > 90 | PASS/FAIL |
| Accessibility (Lighthouse) | XX | > 90 | PASS/FAIL |
| Best Practices (Lighthouse) | XX | > 90 | PASS/FAIL |
| SEO (Lighthouse) | XX | > 90 | PASS/FAIL |
| LCP | X.Xs | < 2.5s | PASS/FAIL |
| INP | XXXms | < 200ms | PASS/FAIL |
| CLS | X.XX | < 0.1 | PASS/FAIL |

## Critical Issues (must fix)
1. [Issue]: [Description] — [Fix guidance]

## Warnings (should fix)
1. [Issue]: [Description] — [Fix guidance]

## Passed Checks
- [List of checks that passed]

## Recommendations
1. [Prioritized list of improvements with expected impact]
```

### Severity Classification

| Severity | Criteria | Examples |
|----------|----------|---------|
| Critical | Blocks users or causes data loss | Missing form labels, keyboard traps, no alt text on functional images |
| High | Significant UX degradation | LCP > 4s, CLS > 0.25, contrast failures on body text |
| Medium | Noticeable quality issue | Missing structured data, unoptimized images, minor CLS |
| Low | Enhancement opportunity | Missing preconnect hints, font subsetting, container queries |

---

## STEP 10: Common Anti-Patterns Reference

Quick reference for the most impactful issues to check and fix.

### Layout Shift Causes
| Anti-Pattern | Fix |
|-------------|-----|
| Images without dimensions | Add `width` and `height` attributes |
| Ads/embeds without reserved space | Set explicit container dimensions |
| Dynamically injected content above viewport | Insert below or use `position: fixed` |
| Web fonts causing FOUT/FOIT | Use `font-display: swap` + `size-adjust` |
| Late-loading CSS changing layout | Inline critical CSS |

### Performance Killers
| Anti-Pattern | Fix |
|-------------|-----|
| Synchronous JS in `<head>` | Add `defer` or `async` attribute |
| Uncompressed images | Convert to WebP/AVIF, set quality 75-85 |
| No code splitting | Split by route, lazy-load below-fold components |
| Unused CSS/JS shipped to client | Tree-shake, purge unused CSS |
| Render-blocking third-party scripts | Load asynchronously, use facades |

### Accessibility Failures
| Anti-Pattern | Fix |
|-------------|-----|
| `<div>` with click handler | Replace with `<button>` |
| Missing alt text | Add descriptive `alt` attribute |
| `outline: none` without replacement | Provide visible focus style |
| Color-only information | Add icons, text labels, or patterns |
| Missing skip-to-content link | Add as first focusable element |
| Inaccessible modal | Trap focus, add Escape handler, use `role="dialog"` |

### SEO Mistakes
| Anti-Pattern | Fix |
|-------------|-----|
| Duplicate title/description | Make unique per page |
| Missing canonical URL | Add `<link rel="canonical">` |
| Client-rendered content only | Add SSR/SSG for content pages |
| Missing structured data | Add JSON-LD for relevant schema types |
| Broken internal links | Audit and fix or add 301 redirects |

---

## CRITICAL RULES

- Always run automated tools first, then supplement with manual checks
- Prioritize fixes by user impact: accessibility and performance before SEO enhancements
- Never remove focus indicators without providing a visible replacement
- Never use ARIA when native HTML semantics are sufficient
- Test on real devices, not just browser DevTools device emulation
- Field data (CrUX, web-vitals) is more valuable than lab data (Lighthouse) for understanding real user experience
- Performance budgets are targets, not limits — treat exceeding them as a bug to fix
- Accessibility is not optional — WCAG 2.1 AA is the legal baseline in many jurisdictions
