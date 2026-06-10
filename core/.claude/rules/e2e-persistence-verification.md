---
description: >
  E2E tests that create records MUST verify actual persistence (per iteration
  in a loop) plus the final rendered UI — never trust a closed dialog/modal or
  an end-of-loop count as success.
globs: ["**/e2e/**/*", "**/tests/e2e/**/*", "**/*.e2e.*", "**/*.spec.ts", "**/*.cy.*"]
version: "1.0.0"
---

# E2E Persistence Verification — a closed dialog is not a saved row

Any E2E test that creates a record MUST verify it actually persisted; a test
that creates more than one record in a loop MUST verify **each iteration**
landed before moving on, AND verify the **final rendered UI** shows all rows.
End-of-loop counts and "dialog closed = success" idioms produce false-positive
passes that hide real persistence bugs.

## Why "dialog/modal closed = success" lies

Most UI dialogs close on the Save click regardless of the mutation outcome. A
validation rejection, an upsert that overwrote an existing row, or a toast
racing the next action — none of these stop the close-assertion from passing.
A bare end-of-loop count catches HTTP-level failures (non-2xx) but MISSES:

- **Upsert with the wrong unique key** that overwrites instead of inserts (the
  count never grows past 1).
- **Form-state pollution** where iteration N+1 submits stale/empty fields and
  the server accepts a malformed row.
- **Stale client cache** where the UI doesn't reflect the DB even though the DB
  is correct.
- **Per-row corruption** — the row persisted, but with the wrong field values.

Per-iteration persistence verification + a final UI render check catches all four.

## MUST / MUST NOT

- MUST gate every Save in a multi-record loop on the **network response**
  (await the create request and assert its status), not on the dialog closing.
- MUST verify persistence **inside the loop** after each insert (a read-back of
  the just-created record, or a DB check). An end-of-loop bulk count is
  insufficient — it misses iterations 2..N when iteration 1's row got overwritten.
- MUST end every multi-record test by reloading the page and asserting the
  visible row count (the reload flushes any optimistic client cache so the
  assertion sees what the user would see).
- MUST NOT use vacuous terminal assertions (`expect(true).toBeTruthy()`, or
  `count >= initialCount`) — they pass when zero rows persisted.
- MUST NOT use "dialog/modal hidden" as the per-iteration success signal.
- MAY skip the UI render check only when the test's stated purpose is API-only
  (e.g. a calculation test that seeds via API deliberately).

## Canonical shape (pseudocode, framework-agnostic)

```
for each record:
    open create form; fill fields
    response = await (submit AND wait-for create-request)   # gate on the response
    assert response.status is the create-success code        # not "dialog closed"
    assert record read-back shows expected values            # per-iteration persistence
reload page; wait for readiness signal                       # flush client cache
assert visible row count == number of records                # final UI render
```

## CRITICAL RULES

- MUST gate each create on the network response status, not on UI dialog close.
- MUST verify persistence per iteration in a loop, plus a final reloaded UI
  row-count assertion.
- MUST NOT use vacuous terminal assertions or "modal closed" as a success signal.
