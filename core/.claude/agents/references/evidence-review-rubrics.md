# Evidence-Derived Review Rubrics

Scoring dimensions for checker agents (`code-reviewer-agent`, `quality-gate-evaluator-agent`),
derived 2026-07-13 from the difference between this hub's known-good merged PRs (clean history,
zero follow-up fixes) and known-bad ones (reverted, or requiring fix-PR chains). Each row cites
its evidence. These are ADDITIVE to the generic dimensions in the agent body — apply both; when
a row here fires, it outranks a clean generic assessment.

Consumers: cited by the checker agents' "Evidence-Derived Review" section. Update this file (not
the agent bodies) when new failure evidence accrues; keep every row evidence-cited — a row nobody
can trace to a real incident is a candidate for deletion, not preservation.

## Rubric rows

| # | Dimension | What to demand | FAIL condition | Severity | Evidence |
|---|---|---|---|---|---|
| R1 | Test-claim reconciliation | A "tested/unit-tested/verified" claim must correspond to a checked-in test file in the SAME diff (or an explicit pointer to the existing test that covers the change) | Claim present, no test path in the file list | Critical | PRs #106, #313 claimed testing with zero test files; #106 then needed 9+ follow-up fix PRs. Good PRs #199/#202 carried real test files |
| R2 | Consumer-effect evidence | Any diff that WIRES an effect through a channel (hook, plugin manifest, injection, notification, analytics tag, cron, CI trigger) must show evidence from the DESTINATION: the injected context visible in a fresh session, the message in the channel, the signal in the live dashboard | Only "it fires / runs without error / is present in config" evidence — artifact-side, never consumer-side | Critical | #142 (SubagentStop context silently dropped, reverted by #150) and #313 (missing `hookEventName`, whole plugin silently inert) — the SAME class twice, 5 weeks apart. #237/#239: config merged clean, GA4 never received a hit for days |
| R3 | Fixture-grounded parsers | Any parser/matcher of an externally-produced format (transcripts, webhooks, API payloads, log shapes) must be tested against CAPTURED REAL samples covering the variant space, checked in as fixtures | Regex/prose detection built from an assumed shape, no real-sample fixture corpus | Critical | #106's transcript-shape regexes: every one of its 9+ follow-up fixes (#118…#332) reactively added exactly one real fixture the original never had |
| R4 | State-lifecycle trace | For every new default/flag/state field: trace the FULL lifecycle — name the code path that transitions it out of its initial value | A dead-end default (no path ever changes it) where the initial value disables the feature's purpose | Critical | #237/#239: `analytics_storage:'denied'` with no grant path — zero collection was the only reachable outcome on 5 live sites |
| R5 | Per-X isolation | Anything described "per-session / per-turn / per-user / per-run" must carry the discriminator in the artifact itself (filename, key, column) — and survive the two-concurrent-instances thought experiment | The described scope is absent from the artifact (a shared file/key doing per-X duty) | High | #217/#231: `.claude/.branch-choice-active` marker called "per-session" had no session-id component; foreseeable from the filename alone |
| R6 | Weakened-test hunt | When test files change alongside code: check for loosened/deleted assertions, silenced tests, widened normalization, grandfather-list growth — each needs a spec citation | Any assertion weakening justified only by the previously-failing run (route `/weakened-test-hunter` for the full taxonomy) | Critical | 2026-04-24 lesson: a test's normalization helper silently accepted a broken YAML form as equivalent, masking a real discovery failure |
| R7 | Sibling-surface enumeration | A fix PR must show the root-cause CLASS was enumerated repo-wide (sweep output or explicitly-filed residual issues), not just the reported instance | Instance-only fix with siblings unexamined (route `/full-defect-surface-sweep`) | High | Recurring multi-wave fix chains: sibling failure classes discovered one PR at a time instead of once |
| R8 | Full-path tracing | Multi-step control-flow changes (orchestration, loops, gates): trace ONE concrete scenario through EVERY branch — including failure and resume paths — before accepting | Only the happy path demonstrated for a change whose correctness is the path structure itself | High | #75 (loop-engineering v1) shipped happy-path-verified and needed 5 named fix rounds (#260–#268) closing batches of path defects found post-merge |
| R9 | Full-gate and live-state evidence | "Verified/done/safe" must cite the project's FULL gate run AFTER the last edit (suite + linters, with counts). Claims about external state (branch open, PR armed, CI pending) must be re-checked live at review time — and a check-suite that is ABSENT is a wedged pipeline, not a pending one | Verification predating the last edit; syntax-check or subset-run presented as the gate; external state asserted from memory | High | Red-PR-via-partial-pytest lesson recurred twice (2026-06-16, 2026-06-19); #351/#354 sat check-suite-less and had to be recreated verbatim as #360/#361 |
| R10 | Substance over shape | Output claimed to come from live/real data must spot-check a join to a source-of-truth row; an adversarially-minded pass on the feature's OWN detection claims (feed it one thing it must catch) | Placeholder/demo/seeded data rendering cleanly and presented as a pass; a detector never fed a known-positive | Critical | 2026-06-25: build-green + size-check both passed while the UI rendered wrong content; 2026-06-21: "tested" survived until an adversarial pass found 2 real bugs in the feature's own detection |

## Standing disciplines (apply on every review, not per-row)

- **Raw-evidence independence** — evaluate ONLY the diff and raw evidence. The dispatching
  prompt's own framing ("this is orphaned", "minor cleanup", "already verified") is a claim to
  re-derive, never an input to inherit. If dispatch supplies conclusions without raw evidence,
  say so and demand the evidence. *(2026-06-19: a reviewer fed the author's framing echoed the
  author's blind spot.)*
- **Deterministic convention pre-pass** — before judgment calls, grep the diff for documented
  platform conventions: `"hooks"` declared in a `plugin.json` (auto-loaded — double-declaring
  errors, broke 3 plugins at once via #237/#244); hook JSON output missing `hookEventName`
  (silently ignored, #313). Cheap, mechanical, catches whole classes.
- **Provenance limit (known blind spot)** — a diff can be clean while the CHANGE ITSELF is
  unauthorized (PR #189 merged after the owner said discard; a pure text review cannot catch
  this). If dispatch context includes intent/approval provenance, check it; if not, note that
  provenance was not reviewable rather than implying it was.

## What PASS looks like (good-PR signals)

- **Pre-merge self-correction on record**: the PR documents bugs found and fixed DURING its own
  live validation (#199 listed 3) — the mirror image of ship-then-discover.
- **Honest under-claiming**: results below the bar reported as below the bar (#202 reported its
  Execute-tier 1/3 finding instead of rounding up).
- **Fixture corpora and consumer-side probes checked in with the feature**, not added reactively
  by later fix PRs.
