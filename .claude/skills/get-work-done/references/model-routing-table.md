# Worker routing table (inlined here so non-hub dispatch sessions never depend on the hub-only
rule file). SSOT: `.claude/rules/model-routing.md` in the hub repo.

**Routing table** (inlined so non-hub sessions don't depend on the hub-only rule; SSOT:
`.claude/rules/model-routing.md`):

| Tier | Contract it for |
|---|---|
| `haiku` | scoring, classification, extraction, format checks, mechanical single-file edits |
| `sonnet` (DEFAULT) | explicit brief + machine-checkable gate: code per plan, tests, research, docs |
| `opus` | deep debugging, architecture, multi-file design freedom - AND preemptively ALL security-category work (scan/audit, vulnerability, exploit-adjacent, authz, prompt-injection) |
| Fable/Mythos | NEVER a worker (preflight exit 4) |

When torn pick the cheaper tier - escalation recovers a wrong cheap pick; a wrong expensive pick
is never detected.
