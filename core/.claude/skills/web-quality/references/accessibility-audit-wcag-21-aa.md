# STEP 3: Accessibility Audit (WCAG 2.1 AA)

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

