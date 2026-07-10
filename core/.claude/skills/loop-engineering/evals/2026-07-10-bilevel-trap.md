# Bilevel self-improvement — Fable-independence trap-test (2026-07-10)

Item 8 of the fable-window program: does the SKILL's FEEDBACK-arm text alone (no
Fable-tier reasoning) drive a cheaper model to MUTATE a stuck loop's search strategy
instead of re-running a proven-failed one?

## Method

- **Fixture:** `evals/fixtures/2026-07-10-stuck-loop-state.json` — a stuck-loop `state.json`
  whose `strategy_ledger["verify_review:test_checkout_total"]` holds **2 recorded failed
  attempts, both `{decomposition: whole, diagnostic: fix-loop, model: sonnet}`** (the naive
  "heal-and-retry the same search" pattern item 8 fixes).
- **Prompt:** a fresh **sonnet** agent given ONLY the updated SKILL FEEDBACK-arm text
  (STEP 6 §6a + mode 1) + the fixture, asked: "you are the loop orchestrator at heal
  cycle 3 — state your next heal dispatch per the skill."
- **PASS bar:** proposes a strategy differing on ≥1 axis from BOTH recorded attempts AND
  cites the novelty gate / mutation rule. **FAIL** if it retries `/fix-loop`+`sonnet`.
- **Samples:** 3 independent sonnet runs; ≥2/3 must pass.

## Result — 3/3 PASS (bar ≥2/3)

Every sample flipped the **diagnostic** axis (`fix-loop → debugging-loop`) — the correct
cheapest-axis-first mutation — kept `model: sonnet` (escalation withheld until ≥2 failures
of the new diagnostic), and cited the novelty gate.

| # | Proposed tuple | Differs from ledger? | Cited novelty/mutation rule? | Verdict |
|---|---|---|---|---|
| 1 | `{whole, debugging-loop, sonnet}` | Yes (diagnostic) | Yes — "mutation rule requires flipping diagnostic first … only 1 distinct strategy has failed so far so escalating to opus would jump the axis order" | PASS |
| 2 | `{whole, debugging-loop, sonnet}` | Yes (diagnostic) | Yes — "Novelty gate passes (not in ledger)"; walked the preference order explicitly | PASS |
| 3 | `{whole, debugging-loop, sonnet}` | Yes (diagnostic) | Yes — "the only tuple not already in `strategy_ledger`"; mutation order diagnostic→decomposition→model | PASS |

### Verbatim verdict excerpts

- **Sample 1:** "`{decomposition: whole, diagnostic: debugging-loop, model: sonnet}` — chosen
  because both ledger entries are the identical `{whole, fix-loop, sonnet}` tuple; the mutation
  rule requires flipping `diagnostic` first (fix-loop → debugging-loop) before touching
  decomposition or escalating model." → `Skill("/debugging-loop", …)`.
- **Sample 2:** "the first not-yet-recorded tuple is obtained by flipping `diagnostic` alone:
  `{whole, debugging-loop, sonnet}`. Novelty gate passes (not in ledger). Model stays at
  `sonnet` … escalation is reserved for after ≥2 supervised failures of a fully-mutated
  strategy set." → `Skill("/debugging-loop", …)`.
- **Sample 3:** "`{decomposition: whole, diagnostic: debugging-loop, model: sonnet}` — the only
  tuple not already in `strategy_ledger` (both prior attempts were `{whole, fix-loop, sonnet}`);
  mutation order flips `diagnostic` before `decomposition` before `model`." → `Skill("/debugging-loop", …)`.

## Conclusion

The FEEDBACK-arm text is Fable-independent for this capability: a cheaper (sonnet) model,
given only the procedure + the ledger, reliably (3/3) refuses to re-run the exhausted
`fix-loop+sonnet` search and instead selects the cheapest novel strategy while citing the
novelty gate. The bilevel mechanism transfers to the model tier the loop actually runs on.
