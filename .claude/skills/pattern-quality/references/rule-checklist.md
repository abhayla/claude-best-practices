# Rule Quality Checklist

## Scope Declaration (exactly one required)

| Scope Type | Declaration | When to Use |
|------------|-------------|-------------|
| Global | `# Scope: global` in first 5 lines | Applies to all files |
| Path-scoped | `globs:` in YAML frontmatter | Applies only to matching files |

MUST NOT have both `# Scope: global` AND `globs: ["**/*"]` — pick one.
MUST NOT leave scope undefined.

## Content Quality

- MUST use directive language (MUST, MUST NOT, NEVER) for critical rules
- MUST provide alternatives for every prohibition — "Use Y instead of X"
- Content lines MUST be >= 5 (no stub rules)
- MUST NOT contain placeholder markers

## Curation Standards

- Every pattern MUST originate from a real correction, observed failure, or documented community pattern
- Before adding, ask: "Has this actually caused a problem, or am I guessing?"
- Provide: source, problem it solves, proof it's not already covered
- Pattern curation is reactive, not speculative

## Writing Rules

- Use RFC 2119 language for critical rules (MUST, NEVER, MUST NOT)
- Avoid vague phrasing (prefer, try to, consider)
- Always provide alternatives with prohibitions
- Use structured tracking (JSON fields) over prose markdown
- Place critical rules in the first 20 lines (positional bias)

## Instruction Budget

| File | Max Lines | Scope |
|------|-----------|-------|
| `~/.claude/CLAUDE.md` | ≤30 | Personal preferences |
| `./CLAUDE.md` | ≤80 | Team conventions |
| `./CLAUDE.local.md` | ≤20 | Personal project overrides |
| Folder-level `CLAUDE.md` | ≤15 | Directory-specific guards |

## Placement Decisions

- If a rule MUST be followed with zero exceptions → convert to a hook
- CLAUDE.md is for "nouns" (architecture, standards); skills for "verbs" (workflows)
- Code style (indentation, semicolons, import order) → delegate to linters via hooks
