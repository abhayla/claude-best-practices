# STEP 2: Core Web Vitals Audit

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
