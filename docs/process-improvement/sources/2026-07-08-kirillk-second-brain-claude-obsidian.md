Source: https://x.com/kirillk_web3/status/2074905017983607081
Captured: 2026-07-08

# kirillk_web3 — "How to Build a Second Brain with Karpathy's Method (Claude + Obsidian)"

**Author:** kirillk_web3 ([@kirillk_web3](https://x.com/kirillk_web3))
**Posted:** 2026-07-08 · **Engagement at capture:** 77 likes, 13 RTs, 70,223 views
**Format:** Single long-form X-native article (~13k chars) — step-by-step build guide with screenshots, ends in an affiliate-hosting pitch.
**Nature:** **Consumer PKM (personal knowledge management) tutorial, not hub-relevant engineering.** Walks through installing Obsidian + Claude Code, writing a `CLAUDE.md` "schema" file, and running an ingest/query/lint loop over a personal notes vault. The "Karpathy's Method" attribution is second-hand (the author cites a Karpathy gist, `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`, but this capture has not independently verified the gist's content or that Karpathy endorses this specific writeup's framing). **Scope caveat:** identical subject to the already-captured Degen_calls_sol piece (same Karpathy "wiki not RAG" framing) — this is effectively a more mechanical, step-by-step restatement of that same idea, not new territory.

---

## What it is

A build tutorial for a personal "second brain": create an Obsidian vault, install Claude Code inside it, write a `CLAUDE.md` that defines three folders (`/raw` for unprocessed sources, `/wiki` for AI-generated atomic notes, plus `index.md` and `log.md`) and three operations — **Ingest** (drop a source in `/raw`, tell Claude to ingest it — it reads, atomizes, links against the existing vault, and files it), **Query** (ask cross-vault questions; answers can be filed back as new pages, closing the loop), and **Lint** (weekly health pass: contradictions, outdated claims, orphan pages, coverage gaps).

## The core argument (same as the already-captured Degen_calls_sol piece)

RAG re-searches from scratch every question and nothing accumulates. A maintained wiki compiles knowledge once, and each new source is linked against everything already there — "Obsidian is the IDE, the LLM is the programmer, the wiki is the codebase." The value is framed as connections growing quadratically with note count (10 notes → 45 possible links; 500 notes → 124,000+), which no human can maintain by hand but an LLM re-linking on every ingest can.

## Mechanical specifics this piece adds over the Degen_calls_sol capture

- Concrete file layout: `/raw`, `/wiki`, `index.md` (catalog), `log.md` (ingestion chronology), `CLAUDE.md` (the schema).
- A "run it 24/7" bonus section: put the vault on a VPS, cron `"ingest this"` hourly against `/raw` so the loop runs even when the local laptop is off — including specific (⚠️ UNVERIFIED, and paired with an affiliate link) VPS pricing (~$10.19/month) and spec recommendations (4 vCPU / 8GB RAM / 80GB SSD).
- A claim that the identical setup runs on "Kimi K2.7" (256K context, reads up to 50 files at once) "for a fraction of the API cost" as a cheaper swap-in for Claude Code — ⚠️ UNVERIFIED (no benchmark or cost figure given, and "Kimi K2.7" is not a model name this capture can confirm exists as stated).

## Relevance to this hub — LOW (conceptual overlap only; no new adoptable mechanics)

Same verdict as the prior capture of this idea: the hub is a Claude Code **patterns factory**, not a personal-notes product, so there is no end-user "second brain" here to build. The honest mapping to existing hub analogues:

| kirillk_web3 concept | Existing hub analogue | Gap? |
|---|---|---|
| `CLAUDE.md` "schema" file the AI reads every session to know how to behave as maintainer | The hub's own `CLAUDE.md` + `.claude/rules/*.md` (auto-loaded directives) — same "instructions read at session start" mechanism, already in place | Covered |
| `/raw` immutable sources + `/wiki` compiled pages + `index.md` catalog | `docs/process-improvement/sources/` (this capture store) is the `/raw`+`/wiki` pattern already; each `INBOX.md` is the `index.md` | Covered — this note IS an instance of the pattern |
| Weekly "lint" pass for orphan pages / stale claims / contradictions | `scripts/check_freshness.py` (age/activity-based staleness) — narrower than a contradiction-aware linter, same gap already noted in the Degen_calls_sol capture below | Partially covered, no new gap surfaced |
| Ingestion log (`log.md`) of what was added and when | `.claude/tasks/lessons.md` + `.remember/` history files (`now.md`/`recent.md`/`archive.md`) serve the equivalent "what happened, when" role for hub state | Covered |
| Session continuity so the loop doesn't restart from zero | `context-management.md` rule 6 (compaction survival) + `/continue`, `/start-session` | Covered |
| Cron'd 24/7 VPS ingestion loop | No hub analogue needed — the hub's automation runs via GitHub Actions cron (`scan-internet.yml`, `aggregate-telemetry.yml`, etc.), not a personal always-on vault | N/A — different problem shape |

**Honest verdict:** this piece adds no new idea beyond the already-captured Degen_calls_sol article — same Karpathy-credited "wiki not RAG" framing, here with a concrete step-by-step folder/file recipe and a VPS-hosting upsell. It confirms (does not deepen) the prior capture's conclusion that the hub already has working analogues (`.remember/`, `check_freshness.py`, `lessons.md`, `docs/process-improvement/`) for every mechanic described, and that the one narrow open idea — a contradiction/orphan-aware linter beyond `check_freshness.py`'s age/activity scope — remains exactly as narrow and non-urgent as previously assessed. The Kimi-K2.7-cost-savings claim and the VPS pricing/spec numbers are marketing-adjacent (affiliate link attached) and unverified; flagged, not acted on.

**No action required.** Consumer PKM tutorial; hub already covers the underlying mechanics via `.remember/`, `check_freshness.py`, and `lessons.md`.

**Cross-links:** [2026-07-04-degen-second-brain-ai-maintained.md](2026-07-04-degen-second-brain-ai-maintained.md) (the same Karpathy-credited idea, captured 4 days earlier as an essay rather than a build tutorial — read that capture's relevance table first, this one does not repeat its reasoning) and [2026-07-08-cyril-claude-projects-full-course.md](2026-07-08-cyril-claude-projects-full-course.md) (Claude Projects as a knowledge-base retrieval mechanism, the adjacent "maintain your knowledge store" theme from the same capture batch).
