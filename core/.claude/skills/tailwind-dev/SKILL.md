---
name: tailwind-dev
description: >
  Tailwind CSS v3/v4 reference: setup and configuration, utility patterns, component
  styling with CVA, theming with CSS custom properties, dark mode, responsive design,
  and performance optimization. Use for styling web applications with Tailwind.
allowed-tools: "Read Grep Glob"
triggers: "tailwind, tailwindcss, utility css, tailwind config, tailwind theme, cn utility"
argument-hint: "<pattern-to-look-up or 'setup' or 'theme' or 'component' or 'migrate'>"
version: "1.0.0"
type: reference
---

# Tailwind CSS Reference

Tailwind CSS v3 and v4 patterns for configuration, component styling, theming, responsive
design, and performance. Covers CVA, tailwind-merge, dark mode, and migration guidance.

**Request:** $ARGUMENTS

---

## Setup & Configuration

### v3: JavaScript Config

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: { brand: { 50: "#eff6ff", 500: "#3b82f6", 900: "#1e3a5a" } },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [require("@tailwindcss/typography"), require("@tailwindcss/forms")],
};
export default config;
```

### v4: CSS-First Config

No JavaScript config needed. All configuration lives in CSS:

```css
/* app.css */
@import "tailwindcss";

@theme {
  --color-brand-50: #eff6ff;
  --color-brand-500: #3b82f6;
  --color-brand-900: #1e3a5a;
  --font-sans: "Inter", "system-ui", "sans-serif";
  --breakpoint-xs: 30rem;
}

@plugin "@tailwindcss/typography";
@plugin "@tailwindcss/forms";
```

No `content` paths needed -- v4 automatically detects source files.

### PostCSS & Framework Integration

```javascript
// v3 postcss.config.mjs                    // v4 postcss.config.mjs
export default {                             export default {
  plugins: {                                   plugins: {
    tailwindcss: {},                              "@tailwindcss/postcss": {},
    autoprefixer: {},                            },
  },                                           };
};
```

**Vite (v4, recommended):** Use `@tailwindcss/vite` instead of PostCSS for fastest builds:
```typescript
// vite.config.ts
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
export default defineConfig({ plugins: [tailwindcss()] });
```

```bash
npm install -D tailwindcss postcss autoprefixer          # v3
npm install -D tailwindcss @tailwindcss/postcss           # v4 (PostCSS)
npm install -D tailwindcss @tailwindcss/vite              # v4 (Vite)
```

## The cn() Utility

Combines `clsx` (conditional class joining) with `tailwind-merge` (conflict resolution):

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

Install: `npm install clsx tailwind-merge`

### Usage Examples

```tsx
import { cn } from "@/lib/utils";

// Conditional classes
<div className={cn("rounded-lg border p-4", isActive && "border-brand-500 bg-brand-50")} />

// Prop-based override -- tailwind-merge resolves bg-white vs bg-gray-100
function Card({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("rounded-lg border bg-white p-6 shadow-sm", className)} {...props} />;
}
<Card className="bg-gray-100" />  {/* bg-white removed, bg-gray-100 wins */}

// Object syntax for multiple conditions
<button className={cn("rounded-md px-4 py-2 font-medium transition-colors", {
  "bg-brand-500 text-white hover:bg-brand-600": variant === "primary",
  "border border-gray-300 bg-white hover:bg-gray-50": variant === "secondary",
  "opacity-50 cursor-not-allowed": disabled,
})} />
```

Without `tailwind-merge`, conflicting classes produce unpredictable results because CSS
specificity depends on stylesheet order, not class order in the HTML attribute.

## Component Variants with CVA

`class-variance-authority` provides typed, declarative variant definitions. Use CVA
instead of manual ternary chains for components with multiple visual states.

```typescript
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-brand-500 text-white hover:bg-brand-600",
        destructive: "bg-red-500 text-white hover:bg-red-600",
        outline: "border border-gray-300 bg-transparent hover:bg-gray-50",
        ghost: "hover:bg-gray-100",
        link: "text-brand-500 underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-lg",
        icon: "h-10 w-10",
      },
    },
    compoundVariants: [{ variant: "outline", size: "sm", className: "border-2" }],
    defaultVariants: { variant: "default", size: "md" },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
export { Button, buttonVariants };
```

Install: `npm install class-variance-authority`

```tsx
<Button variant="destructive" size="lg">Delete</Button>
<Button variant="outline">Cancel</Button>
<Button className="w-full">Full Width</Button>
```

## Responsive Design

Mobile-first breakpoint system. Unprefixed utilities apply at all sizes; prefixed
utilities apply at that breakpoint and above.

| Prefix | Min-width | Typical device |
|--------|-----------|----------------|
| `sm`   | 640px     | Large phones   |
| `md`   | 768px     | Tablets        |
| `lg`   | 1024px    | Laptops        |
| `xl`   | 1280px    | Desktops       |
| `2xl`  | 1536px    | Large screens  |

```html
<div class="flex flex-col md:flex-row lg:gap-8">
  <aside class="w-full md:w-64 lg:w-80">Sidebar</aside>
  <main class="flex-1">Content</main>
</div>

<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <!-- responsive card grid -->
</div>

<h1 class="text-2xl sm:text-3xl lg:text-5xl font-bold">Heading</h1>
```

### Container Queries (v4 built-in, v3 via plugin)

Style based on parent container size instead of viewport. Use viewport queries for page
layout, container queries for reusable component internals:

```html
<div class="@container">
  <div class="flex flex-col @md:flex-row @lg:gap-6">
    <img class="w-full @md:w-48" src="..." alt="..." />
    <div class="@md:flex-1">Adapts to container, not viewport</div>
  </div>
</div>
```

### Arbitrary Breakpoints (v4)

```html
<div class="min-[420px]:text-center max-[600px]:bg-sky-100">One-off breakpoint</div>
```

## Dark Mode & Theming

### Class-Based Dark Mode

```html
<html class="dark">
  <body class="bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
    <p class="text-gray-600 dark:text-gray-400">Adapts to theme.</p>
  </body>
</html>
```

**v3:** `darkMode: "class"` in `tailwind.config.ts`
**v4:** Built-in via `prefers-color-scheme`. For manual class toggle:
```css
@custom-variant dark (&:where(.dark, .dark *));
```

### CSS Custom Properties for Theme Tokens

Define semantic tokens that swap automatically without `dark:` prefixes:

```css
@import "tailwindcss";

@theme {
  --color-surface: var(--surface);
  --color-on-surface: var(--on-surface);
  --color-primary: var(--primary);
  --color-on-primary: var(--on-primary);
  --color-muted: var(--muted);
}

:root {
  --surface: #ffffff; --on-surface: #0f172a;
  --primary: #3b82f6; --on-primary: #ffffff;
  --muted: #94a3b8;
}
.dark {
  --surface: #0f172a; --on-surface: #f1f5f9;
  --primary: #60a5fa; --on-primary: #0f172a;
  --muted: #64748b;
}
```

```html
<div class="bg-surface text-on-surface">
  <button class="bg-primary text-on-primary">Action</button>
</div>
```

### Multiple Themes with Data Attributes

```css
[data-theme="ocean"] {
  --surface: #0c1222; --on-surface: #e2e8f0;
  --primary: #06b6d4; --on-primary: #0c1222;
}
[data-theme="forest"] {
  --surface: #0f1a0f; --on-surface: #d9f2d9;
  --primary: #22c55e; --on-primary: #0f1a0f;
}
```

Toggle: `document.documentElement.setAttribute("data-theme", "ocean")`

## Dynamic Classes

### NEVER Concatenate Class Names

String interpolation breaks class detection -- tree-shaking removes unrecognized classes:

```typescript
// WRONG -- purged because Tailwind cannot detect classes statically
<div className={`bg-${color}-500 text-${color}-100`} />

// CORRECT -- complete strings via mapping object
const colorMap = {
  success: "bg-green-500 text-green-100",
  error: "bg-red-500 text-red-100",
  warning: "bg-amber-500 text-amber-900",
  info: "bg-blue-500 text-blue-100",
} as const;

type ColorKey = keyof typeof colorMap;
function Badge({ color, children }: { color: ColorKey; children: React.ReactNode }) {
  return <span className={cn("rounded-full px-2 py-1 text-xs font-medium", colorMap[color])}>{children}</span>;
}
```

### Safelisting (Use Sparingly)

**v3:** `safelist: [{ pattern: /^bg-(red|green|blue)-(100|500|900)$/ }]` in config
**v4:** `@source "../data/colors.ts";` to force-scan additional paths

## Performance

- **Content paths (v3):** Scope `content` globs tightly -- avoid `"./**/*"`
- **v4 auto-detection:** No manual paths needed; use `@source` for paths outside project root
- **Avoid `@apply` as default** -- it is an escape hatch for extracting combinations repeated 5+ places that cannot become components. Prefer component composition.
- **v4 Oxide engine:** Rust-based, 2-5x faster builds than v3
- **Use `@tailwindcss/vite`** over PostCSS when your bundler supports it

## v3 to v4 Migration

```bash
npx @tailwindcss/upgrade
```

### Key Changes

| Area | v3 | v4 |
|------|-----|-----|
| Config | `tailwind.config.ts` (JS) | `@theme {}` in CSS |
| Content paths | Manual `content: [...]` | Automatic detection |
| Custom colors | `theme.extend.colors` | `@theme { --color-*: value }` |
| Plugins | `require("@tailwindcss/...")` in JS | `@plugin "..."` in CSS |
| Dark mode | `darkMode: "class"` in config | Built-in; `@custom-variant` for manual toggle |
| PostCSS plugin | `tailwindcss` | `@tailwindcss/postcss` |
| Custom utilities | JS plugin API | `@utility` directive in CSS |
| Gradients | `bg-gradient-to-*` | `bg-linear-to-*` |
| Default border | `gray-200` | `currentColor` |
| Container queries | Plugin required | Built-in |
| Browser support | Broad | Safari 16.4+, Chrome 111+, Firefox 128+ |

### Migration Examples

**Custom colors:** `theme.extend.colors.brand.500` becomes `@theme { --color-brand-500: #3b82f6; }`

**Custom utility (v4):**
```css
@utility content-auto {
  content-visibility: auto;
}
/* Supports all variants automatically: hover:content-auto, md:content-auto */
```

**Gradient rename:** `bg-gradient-to-r` becomes `bg-linear-to-r`

**Dark mode (v4):** Replace `darkMode: "class"` config with `@custom-variant dark (&:where(.dark, .dark *));` in CSS

## CRITICAL RULES

- **Never concatenate class names dynamically** -- use complete strings via mapping objects or safelisting. `bg-${color}-500` breaks tree-shaking.
- **`@apply` is an escape hatch, not the default** -- prefer utility classes in markup and component extraction for reuse.
- **Use `tailwind-merge` when combining conditional classes** -- without it, conflicting utilities produce unpredictable results.
- **Use CVA for component variants** -- never build variant logic with chains of ternary operators. CVA provides type safety, defaults, and compound variants.
- **v4: prefer CSS-first config (`@theme`)** -- the JS config file is a legacy compatibility layer. New projects MUST use CSS-first configuration.
- **Mobile-first responsive design** -- unprefixed utilities define mobile layout; use `sm:`, `md:`, `lg:` to layer larger-screen styles.
- **Use container queries for component-level responsiveness** -- viewport breakpoints for page layout, `@container` for reusable component internals.
