# Scope: global

# Definition-of-Done Verbs Are Load-Bearing

version: "1.0.0"

When you write an acceptance criterion, task, or definition of done, the **verb
and its completeness bar are load-bearing** — an implementer (and especially an
autonomous executor running unattended) will satisfy the **weakest defensible
reading** of whatever you wrote. Vague done-criteria don't fail loudly; they get
"met" in a way you didn't intend.

## The failure this kills

"Report the score" was satisfied by printing *a* score — at the weakest reading
— when the intent was "compute and surface the score for the default case."
"Cards are represented" was met by rendering one card when the intent was "all
N×M cards render." The criterion wasn't wrong; it was **under-specified**, so the
cheapest path to a literal checkmark won.

## How to write a load-bearing criterion

Every acceptance criterion MUST state two things explicitly:

1. **The ACTION** — the specific verb, disambiguated. Prefer precise verbs over
   elastic ones: `compute and display` / `persist and read back` / `verify for
   every member` — not `handle`, `support`, `report`, `cover`, `represent`,
   which each admit a trivially-weak reading.
2. **The COMPLETENESS BAR** — the scope over which the action must hold: *which*
   inputs, *which* path (the default/product path, not a convenient one — see
   `output-plausibility-verification.md`), *how many* (all N, not "some"), and
   the observable signal that proves it.

> Weak: "Report the FIRE number."
> Load-bearing: "Compute the FIRE number on the default view and assert it falls
> in a domain-sane range; the rendered value matches the API value within 1%."

## CRITICAL RULES

- MUST state both the ACTION (precise verb) and the COMPLETENESS BAR (which
  inputs / which path / how many / what observable signal) in every acceptance
  criterion or definition of done.
- MUST NOT use elastic verbs (`handle`, `support`, `report`, `cover`,
  `represent`, `work`) without pinning what "done" observably means — an
  unattended executor will satisfy the weakest reading.
- MUST anchor the completeness bar to the **default product path**, not a
  convenient configuration.
