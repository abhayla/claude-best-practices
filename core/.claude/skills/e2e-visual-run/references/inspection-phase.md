# Inspection Phase: Dual-Signal Visual Verification

Detailed guidance for STEP 4 of the e2e-visual-run skill.

## Accessibility Tree Verification Checklist

### Structural Checks
- [ ] Page has at least one `<main>` landmark
- [ ] Headings follow hierarchy (no skipped levels: h1 → h3)
- [ ] All interactive elements (buttons, links, inputs) have accessible names
- [ ] Form inputs have associated labels (via `aria-label`, `aria-labelledby`, or `<label>`)
- [ ] No duplicate `id` attributes
- [ ] Images have `alt` text (or `role="presentation"` for decorative)

### State Checks
- [ ] No elements with `aria-busy="true"` (page still loading)
- [ ] Disabled elements have `aria-disabled="true"` (not just visual styling)
- [ ] Selected/active tabs have `aria-selected="true"`
- [ ] Expandable sections reflect correct `aria-expanded` state
- [ ] Error messages linked via `aria-describedby` or `role="alert"`

### Data Population Checks
- [ ] Tables have `<th>` headers and data rows (not empty)
- [ ] Lists have at least one item (unless empty state is expected)
- [ ] Form fields contain expected default values
- [ ] Navigation links are present and labeled

## Screenshot AI Review Criteria

When no baseline exists, verify these visually:

### Layout
- No overlapping elements
- Content within viewport (no horizontal scroll unless intended)
- Responsive breakpoints render correctly
- Footer at bottom, header at top

### Data
- Tables have visible data rows (not just headers)
- Charts have rendered data points (not empty canvases)
- Cards/tiles populated with content
- Numbers/metrics displayed (not "NaN", "undefined", "$0.00" unexpectedly)

### Error States
- No error dialogs or crash screens
- No uncaught exception banners
- No "404" or "500" error pages
- No "Something went wrong" messages

### Visual Quality
- Text is readable (not truncated, not overflowing containers)
- Icons rendered (not broken image placeholders)
- Colors applied (not unstyled/white-on-white)
- Loading states resolved (no spinners, skeletons, or progress bars)

## Dynamic Content Patterns

These patterns cause false negatives. Check before flagging as FAILED:

| Pattern | Detection Method | Action |
|---------|-----------------|--------|
| Timestamps | Text matching `\d{4}-\d{2}-\d{2}` or relative time ("5m ago") | Ignore in comparison |
| Random avatars | `<img>` with `gravatar`, `avatar`, `placeholder` in src | Ignore region |
| Loading spinners | `aria-busy="true"` or `role="progressbar"` in a11y tree | Wait 3s, re-capture |
| Animations | CSS `animation` or `transition` properties active | Wait for `transitionend` event |
| Randomized order | List items present but in different order | Compare as sets, not sequences |
| Session tokens | Dynamic URL parameters or cookies in page content | Ignore |

## Confidence Scoring

Rate each verdict 0.0-1.0:

| Confidence | Range | Criteria |
|-----------|-------|----------|
| HIGH | 0.9-1.0 | Both signals agree clearly, no dynamic content ambiguity |
| MEDIUM | 0.7-0.9 | One signal ambiguous (e.g., dynamic content in screenshot) |
| LOW | <0.7 | Both signals ambiguous — flag for human review |

Low-confidence verdicts should be logged as warnings in the final report,
not treated as hard failures.
