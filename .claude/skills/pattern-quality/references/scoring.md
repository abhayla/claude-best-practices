# Quality Score Criteria

Rate each pattern 0-100 based on checklist compliance:

| Score | Grade | Meaning |
|-------|-------|---------|
| 90-100 | A | Fully compliant, exemplary |
| 75-89 | B | Minor gaps (warnings, not failures) |
| 60-74 | C | Multiple warnings, needs attention |
| 40-59 | D | Has FAIL items, must not ship |
| 0-39 | F | Fundamentally non-compliant |

New patterns MUST score >= 75 (Grade B or higher).
The score is advisory — the pass/fail checks in the checklists are authoritative.

## Incremental Adoption

Existing patterns that predate quality standards MAY have violations:
- Fix violations in the section you are modifying
- Do not rewrite the entire file just to fix pre-existing violations
- When a pattern is modified for any reason, bring the ENTIRE file up to standard before committing
- New patterns MUST pass all checks with zero violations from the start
