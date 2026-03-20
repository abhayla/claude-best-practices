# STEP 6: Responsive Design Audit

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

