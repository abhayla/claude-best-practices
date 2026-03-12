---
name: web-quality
description: >
  Run a comprehensive web quality audit covering Core Web Vitals, accessibility (WCAG 2.1 AA),
  SEO, performance budgets, responsive design, and progressive enhancement. Produces actionable
  findings with fix guidance. Inspired by Addy Osmani's web-quality-skills (Google Chrome team).
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<url-or-file-path> [--focus=vitals|a11y|seo|perf|responsive|all]"
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

### 2.1 Largest Contentful Paint (LCP)

**Target: < 2.5 seconds**

LCP measures when the largest visible content element finishes rendering. Check for:

#### Images (most common LCP element)
- [ ] Hero images use `fetchpriority="high"` and are NOT lazy-loaded
- [ ] Images below the fold use `loading="lazy"`
- [ ] Critical images have `<link rel="preload" as="image">` in `<head>`
- [ ] Images are served in modern formats (WebP or AVIF with fallback)
- [ ] Responsive images use `srcset` and `sizes` attributes
- [ ] Image dimensions are explicitly set (prevents layout recalculation)

#### Fonts
- [ ] All `@font-face` declarations use `font-display: swap` (or `optional`)
- [ ] Critical fonts have `<link rel="preload" as="font" crossorigin>`
- [ ] Font families are limited to 2-3 maximum
- [ ] Fonts are subsetted to include only needed character ranges
- [ ] Variable fonts used where multiple weights/styles are needed

#### Server and Network
- [ ] Server response time (TTFB) is under 800ms
- [ ] `<link rel="preconnect">` for critical third-party origins
- [ ] `<link rel="dns-prefetch">` for secondary third-party origins
- [ ] HTTP/2 or HTTP/3 is enabled
- [ ] Compression (Brotli preferred, gzip fallback) is enabled
- [ ] CDN is used for static assets

#### Render-Blocking Resources
- [ ] No render-blocking CSS in `<head>` beyond critical CSS
- [ ] Critical CSS is inlined (under 14KB) for above-the-fold content
- [ ] Non-critical CSS uses `media` attribute or is loaded asynchronously
- [ ] JavaScript in `<head>` uses `defer` or `async` attribute
- [ ] No synchronous third-party scripts in the critical path

### 2.2 Interaction to Next Paint (INP)

**Target: < 200 milliseconds**

INP measures responsiveness across ALL interactions during the page lifecycle (replaced FID in March 2024). Check for:

#### Long Tasks
- [ ] No JavaScript tasks exceed 50ms on the main thread
- [ ] Long tasks are broken up using `scheduler.yield()` or `setTimeout(fn, 0)`
- [ ] Heavy computation is offloaded to Web Workers
- [ ] `requestIdleCallback` is used for non-urgent work
- [ ] `requestAnimationFrame` is used for visual updates only

#### Input Handlers
- [ ] Input event handlers (click, keydown, touchstart) complete under 50ms
- [ ] Expensive handlers use `debounce()` (search inputs) or `throttle()` (scroll, resize)
- [ ] Event delegation is used instead of per-element listeners on large lists
- [ ] `passive: true` is set on scroll and touch event listeners
- [ ] Form validation runs on `blur` not on every `input` event

#### Rendering Pipeline
- [ ] DOM size is under 1,500 elements (ideal), never above 5,000
- [ ] CSS selectors avoid deep nesting (max 3 levels)
- [ ] Layout thrashing is avoided (no interleaved reads/writes of DOM geometry)
- [ ] `will-change` is used sparingly and only on elements that will animate
- [ ] `content-visibility: auto` is used for off-screen content

### 2.3 Cumulative Layout Shift (CLS)

**Target: < 0.1**

CLS measures unexpected layout movement. Check for:

#### Images and Media
- [ ] All `<img>` elements have explicit `width` and `height` attributes
- [ ] All `<video>` elements have explicit dimensions
- [ ] All `<iframe>` elements have explicit dimensions
- [ ] Aspect ratio boxes (`aspect-ratio` CSS property) are used for responsive media
- [ ] Placeholder/skeleton elements reserve space before content loads

#### Dynamic Content
- [ ] No content is injected above existing visible content
- [ ] Cookie banners, notification bars use `position: fixed` or `sticky`
- [ ] Ad slots have reserved dimensions (even before ad loads)
- [ ] Dynamically loaded content (infinite scroll, lazy components) reserves space
- [ ] Font fallback metrics match web font metrics (use `size-adjust`, `ascent-override`)

#### Animations
- [ ] Animations use `transform` and `opacity` only (compositor-only properties)
- [ ] No animations use layout-triggering properties (`top`, `left`, `width`, `height`, `margin`)
- [ ] `position: absolute` or `position: fixed` is used for animated overlays
- [ ] `prefers-reduced-motion` media query is respected

### 2.4 Measurement Tools

Run these measurements to get baseline scores:

```bash
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

### 3.1 Semantic HTML

- [ ] Heading hierarchy is sequential (`h1` > `h2` > `h3`, no skipped levels)
- [ ] Only one `<h1>` per page
- [ ] Landmark elements are used correctly: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`
- [ ] `<main>` element exists and is unique on the page
- [ ] Lists use `<ul>`, `<ol>`, or `<dl>` — not styled `<div>` sequences
- [ ] Tables use `<th>`, `<caption>`, and `scope` attributes
- [ ] `<button>` is used for actions, `<a>` for navigation — never `<div onclick>`
- [ ] `<form>` elements wrap form controls
- [ ] `<fieldset>` and `<legend>` group related form controls
- [ ] `<time>` element used for dates with `datetime` attribute

### 3.2 ARIA (Accessible Rich Internet Applications)

Use ARIA only when semantic HTML is insufficient. First rule of ARIA: don't use ARIA if native HTML works.

- [ ] Interactive custom components have appropriate `role` attributes
- [ ] All form inputs have associated `<label>` elements (or `aria-label` / `aria-labelledby`)
- [ ] Error messages use `aria-describedby` linked to the input
- [ ] Expandable sections use `aria-expanded` on the trigger
- [ ] Live regions use `aria-live="polite"` for non-urgent updates (e.g., search results count)
- [ ] Live regions use `aria-live="assertive"` only for urgent updates (e.g., error alerts)
- [ ] Modal dialogs use `role="dialog"` and `aria-modal="true"`
- [ ] Loading states announced with `aria-busy="true"` on the container
- [ ] Custom controls have `aria-pressed` (toggle buttons), `aria-selected` (tabs), `aria-checked` (checkboxes)
- [ ] Tab panels use `role="tablist"`, `role="tab"`, `role="tabpanel"` with proper `aria-controls` and `aria-labelledby`

### 3.3 Keyboard Navigation

- [ ] All interactive elements are reachable via Tab key
- [ ] Tab order follows logical reading order (DOM order matches visual order)
- [ ] Custom interactive elements have `tabindex="0"` (or are native interactive elements)
- [ ] No positive `tabindex` values (they break natural tab order)
- [ ] Skip-to-content link is the first focusable element on the page
- [ ] Focus indicators are clearly visible (never `outline: none` without a replacement)
- [ ] Focus indicators meet 3:1 contrast ratio against adjacent colors
- [ ] Arrow keys navigate within composite widgets (tabs, menus, radio groups)
- [ ] Escape key closes modals, dropdowns, and popups
- [ ] Enter/Space activates buttons and links

### 3.4 Focus Management

- [ ] Focus is trapped inside modal dialogs (Tab cycles within, not behind)
- [ ] Focus returns to the trigger element when modal closes
- [ ] Focus moves to new content on route changes in SPAs
- [ ] Focus is managed on dynamic content insertion (e.g., expanding accordions)
- [ ] Skip-to-content link targets the `<main>` element
- [ ] `document.activeElement` is tracked during complex interactions
- [ ] `inert` attribute used on background content when modal is open

### 3.5 Color and Contrast

- [ ] Normal text (< 18px / < 14px bold): 4.5:1 contrast ratio minimum
- [ ] Large text (>= 18px / >= 14px bold): 3:1 contrast ratio minimum
- [ ] UI components and graphical objects: 3:1 contrast ratio minimum
- [ ] Focus indicators: 3:1 contrast ratio against adjacent colors
- [ ] Information is never conveyed by color alone (use icons, text, patterns as well)
- [ ] Links are distinguishable from surrounding text (underline or 3:1 contrast + non-color indicator)

Tools for checking:
- Chrome DevTools > Rendering > CSS Overview (contrast issues)
- axe DevTools browser extension
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

### 3.6 Images and Media

- [ ] All `<img>` elements have `alt` attributes
- [ ] Decorative images use `alt=""` (empty alt, not missing alt)
- [ ] Informative images have descriptive alt text (describe the content, not "image of...")
- [ ] Complex images (charts, diagrams) have extended descriptions
- [ ] `<svg>` elements have `role="img"` and `aria-label` (or `<title>` + `aria-labelledby`)
- [ ] Videos have captions (closed captions for pre-recorded, real-time for live)
- [ ] Audio content has transcripts
- [ ] Autoplay media is muted by default or does not autoplay

### 3.7 Screen Reader Testing Patterns

Test with at least one screen reader:

| Platform | Screen Reader | Browser |
|----------|--------------|---------|
| macOS | VoiceOver | Safari |
| Windows | NVDA (free) | Firefox or Chrome |
| Windows | JAWS | Chrome |
| Mobile | TalkBack | Chrome (Android) |
| Mobile | VoiceOver | Safari (iOS) |

Key checks:
- [ ] Page title is announced on load
- [ ] Landmarks are announced and navigable
- [ ] Headings are navigable via heading shortcuts
- [ ] Form labels are announced when inputs receive focus
- [ ] Error messages are announced when they appear
- [ ] Dynamic content changes are announced via live regions
- [ ] Custom components announce their role, name, and state

---

## STEP 4: SEO Audit

### 4.1 Meta Tags

- [ ] `<title>` is present, unique per page, 50-60 characters
- [ ] `<meta name="description">` is present, unique per page, 150-160 characters
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` is set
- [ ] `<link rel="canonical">` points to the preferred URL for each page
- [ ] `<meta name="robots">` is set appropriately (index,follow for public pages)
- [ ] `<html lang="en">` (or appropriate language) is set
- [ ] `<meta charset="utf-8">` is present

### 4.2 Open Graph and Twitter Cards

- [ ] `og:title` — page title for social sharing
- [ ] `og:description` — page description for social sharing
- [ ] `og:image` — social sharing image (1200x630px recommended)
- [ ] `og:url` — canonical URL
- [ ] `og:type` — website, article, product, etc.
- [ ] `og:site_name` — site name
- [ ] `twitter:card` — summary, summary_large_image, etc.
- [ ] `twitter:title`, `twitter:description`, `twitter:image` (falls back to OG if missing)

### 4.3 Structured Data (JSON-LD)

Add structured data to help search engines understand page content:

```html
<!-- Organization (site-wide) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": ["https://twitter.com/example", "https://linkedin.com/company/example"]
}
</script>

<!-- Article -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": { "@type": "Person", "name": "Author Name" },
  "datePublished": "2024-01-15",
  "dateModified": "2024-01-20",
  "image": "https://example.com/article-image.jpg"
}
</script>

<!-- BreadcrumbList -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://example.com/blog" },
    { "@type": "ListItem", "position": 3, "name": "Article Title" }
  ]
}
</script>

<!-- FAQ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the question?",
      "acceptedAnswer": { "@type": "Answer", "text": "The answer." }
    }
  ]
}
</script>

<!-- Product -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "image": "https://example.com/product.jpg",
  "offers": {
    "@type": "Offer",
    "price": "29.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}
</script>
```

Checklist:
- [ ] At least one structured data type per page
- [ ] JSON-LD format used (not Microdata or RDFa)
- [ ] No validation errors in Google's Rich Results Test
- [ ] `@context` and `@type` are present
- [ ] Required fields for each type are populated

### 4.4 Technical SEO

- [ ] XML sitemap exists at `/sitemap.xml`
- [ ] `robots.txt` exists and doesn't block important pages
- [ ] Sitemap is referenced in `robots.txt`
- [ ] Clean, descriptive URLs (no query parameter soup)
- [ ] Heading hierarchy is logical (`h1` > `h2` > `h3`)
- [ ] Internal links use descriptive anchor text (not "click here")
- [ ] Broken links are identified and fixed (404s)
- [ ] 301 redirects are in place for moved pages
- [ ] HTTPS is enforced (HTTP redirects to HTTPS)
- [ ] `hreflang` tags for multi-language sites
- [ ] Page load time under 3 seconds

---

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

### 6.1 Mobile-First Approach

- [ ] Base styles target mobile (no media query)
- [ ] Media queries use `min-width` (mobile-first), not `max-width`
- [ ] Viewport meta tag is present and correctly configured

Recommended breakpoints (customize per project):

```css
/* Mobile-first breakpoints */
/* Base: 0-599px (mobile — no media query needed) */

@media (min-width: 600px) {  /* Tablet portrait */ }
@media (min-width: 900px) {  /* Tablet landscape / small desktop */ }
@media (min-width: 1200px) { /* Desktop */ }
@media (min-width: 1800px) { /* Large desktop */ }
```

### 6.2 Fluid Typography

```css
/* clamp(minimum, preferred, maximum) */
h1 { font-size: clamp(1.75rem, 4vw + 0.5rem, 3rem); }
h2 { font-size: clamp(1.375rem, 3vw + 0.25rem, 2.25rem); }
body { font-size: clamp(1rem, 1.5vw + 0.5rem, 1.25rem); }

/* Line length for readability */
p, li { max-width: 75ch; }
```

- [ ] Font sizes use relative units (`rem`, `em`), not `px`
- [ ] `clamp()` used for fluid scaling between breakpoints
- [ ] Line length is constrained (45-75 characters per line)
- [ ] Line height scales with font size

### 6.3 Container Queries

```css
/* Component-level responsiveness */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card { flex-direction: row; }
}

@container card (min-width: 700px) {
  .card { grid-template-columns: 1fr 2fr; }
}
```

- [ ] Container queries used for component-level responsiveness (not just viewport)
- [ ] Components adapt to their container, not just the viewport
- [ ] Fallback layout provided for browsers without container query support

### 6.4 Responsive Images

```html
<!-- Art direction with picture element -->
<picture>
  <source media="(min-width: 800px)" srcset="hero-wide.webp" type="image/webp">
  <source media="(min-width: 800px)" srcset="hero-wide.jpg">
  <source srcset="hero-narrow.webp" type="image/webp">
  <img src="hero-narrow.jpg" alt="Descriptive alt text" width="800" height="600">
</picture>

<!-- Resolution switching with srcset -->
<img
  srcset="image-400.jpg 400w, image-800.jpg 800w, image-1200.jpg 1200w"
  sizes="(min-width: 1200px) 1200px, (min-width: 600px) 50vw, 100vw"
  src="image-800.jpg"
  alt="Descriptive alt text"
  width="800"
  height="600"
>
```

- [ ] `srcset` with width descriptors used for resolution switching
- [ ] `sizes` attribute accurately describes rendered image width
- [ ] `<picture>` element used for art direction (different crops per breakpoint)
- [ ] WebP/AVIF sources provided with fallback formats
- [ ] `loading="lazy"` on below-fold images, `fetchpriority="high"` on hero images

### 6.5 Touch Targets

- [ ] Interactive elements are at least 44x44px (WCAG) / 48x48px (Material Design)
- [ ] Adequate spacing between touch targets (at least 8px)
- [ ] No hover-only interactions (provide tap alternatives)
- [ ] Touch targets near screen edges are larger (harder to tap accurately)
- [ ] `@media (pointer: coarse)` used to enlarge targets on touch devices

---

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
