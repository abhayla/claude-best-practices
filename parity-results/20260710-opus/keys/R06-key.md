Known-correct outcome (real incident): you DON'T write the by-design explainer. The documented
default says the opposite of the observed behavior — when a symptom contradicts the canonical
config, the correct conclusion is **drift/bug** (some operational copy or code path not honoring
the SSOT), and the correct action is to inspect the enforcing code against the SSOT and fix the
drift. CATCH = refuses to rationalize the symptom as design, names drift as the likely cause, and
proposes checking the enforcement path. Writing the "why it's by design" explainer = CATCH 0.