# Scope: global

# Code Readability & Maintainability

Universal readability standards that apply to all code in this project, regardless of language. Code formatting (indentation, semicolons, import order) is enforced by linters/formatters via hooks (see `configuration-ssot.md`) — this rule covers the judgment-requiring concerns that tools cannot check.

## Top-Level MUST NOTs

- MUST NOT use names that require a mental decode step (single-letter variables outside tight scopes, abbreviations without domain precedent, misleading names like `data` / `info` / `manager`)
- MUST NOT mix levels of abstraction within a single function — callers of a high-level intent MUST NOT see low-level byte manipulation inline
- MUST NOT leave code in a worse state than you found it — the Boy Scout Rule applies to every touched file

## Meaningful Names

Names of variables, functions, classes, and modules MUST reveal intent without requiring a comment to explain. Cognitive load is the dominant cost of reading code — bad names make every reader pay.

- Use domain vocabulary — name a class `Invoice` if the business calls it an invoice, not `BillingDataItem`
- Function names are verb phrases (`calculateTotal`, `fetchUser`); class names are noun phrases (`OrderValidator`); boolean names are predicates (`isEmpty`, `hasExpired`)
- Avoid disinformation — `accountList` MUST be a list, not a set; `userMap` MUST be a map
- Replace magic abbreviations — `usr_mgr` is shorter but `userManager` is clearer; shortness is rarely worth ambiguity
- Scope-length correlation: one-letter names are acceptable inside a 3-line lambda, intolerable in a 50-line function
- Search-ability: `MAX_CLASSES_PER_STUDENT` can be grep'd across the codebase; `7` cannot
- Exception: well-known domain acronyms (`HTTP`, `URL`, `API`, `DB`) and mathematical conventions (`i`, `j` for loop indices, `x`, `y` for coordinates)

## Small Functions / Single Level of Abstraction

Functions MUST do one thing and do it at one consistent level of abstraction. When a function mixes business intent with low-level implementation (loops, string parsing, byte shuffling), extract the low-level parts to named helpers.

- Target size: most functions under 20 lines; a function over 50 lines is a refactoring signal
- One return value shape per function — returning `Result<T> | null | undefined | string` from the same function is a lie to the caller
- Cyclomatic complexity heuristic: more than 10 decision points (if/else/switch/&&/||) in a single function is a signal to extract
- Extract named helpers over inline comments — a function name is a comment that cannot drift from the code
- Nested depth: >3 levels of indentation inside a function is a signal; use early returns / guard clauses to flatten

## Boy Scout Rule

Leave the code cleaner than you found it. Every touched file gets a small, safe improvement that does not expand the scope of the change.

- Rename a confusing local variable, extract a magic number, delete a dead branch
- MUST keep Boy Scout changes minimal and reviewable — do not bundle a refactor into a bug fix beyond what's trivially safe
- MUST NOT reformat untouched code in a way that creates unrelated diff noise — the review should see the intent, not a whitespace churn

## Comment Discipline (Cross-Reference)

Comment policy is owned by `claude-behavior.md` rule 7 (No Redundant Comments) — see that rule for the authoritative constraint.

## Code Formatting (Cross-Reference)

Code style (indentation, braces, import order, line length) is enforced by linters / formatters via hooks — see `configuration-ssot.md` rule 3. This rule MUST NOT duplicate style guidance; if a formatter can enforce it, it belongs in a hook, not in a rule.

## Readability vs. Cleverness

The reader's time costs more than the writer's. Given two implementations that solve the same problem at the same performance cost, MUST choose the one that reads more obviously.

- Prefer straightforward code over clever code
- Prefer named intermediate variables over one-liner chains — `const adults = users.filter(isAdult)` reads better than an inline `users.filter(u => u.age >= 18)`
- Reserve clever tricks for documented hot paths where a profiler proved the simpler form was too slow

## CRITICAL RULES

- MUST NOT ship names that require a comment to explain — rename instead of documenting
- MUST NOT mix abstraction levels in a single function — extract to named helpers
- MUST leave touched files slightly cleaner (Boy Scout Rule), without bundling unrelated refactors
- MUST prefer a good name over a comment
- MUST NOT re-implement formatting rules here — delegate to linters/formatters via hooks
