# STEP 6: Handle Disagreements

### 6.1 Disagreement Response Protocol

**Round 1 — Present your reasoning:**

```
I see the concern, but I believe the current approach is better here because:

1. {Reason with evidence — benchmarks, docs, codebase precedent}
2. {Additional supporting point}

{If applicable: "Here is an alternative that might address your concern
differently: {alternative}"}
```

**Round 2 — If the reviewer pushes back:**

```
I understand your perspective. Let me address the specific points:

{Point-by-point response to the reviewer's counter-arguments.}

{Propose a compromise if possible: "What if we {compromise approach}? This
addresses {reviewer's concern} while preserving {your concern}."}
```

**Round 3 — Escalate:**

If disagreement persists after two rounds, do NOT continue arguing in the PR thread.

```
We have different perspectives on this. To avoid blocking the PR, I suggest one
of:
1. Sync offline (call/Slack) to discuss the trade-offs in real-time
2. Bring in a third reviewer (@{suggested_person}) for a tiebreaker
3. Merge with a TODO and revisit in a follow-up PR with more data

@{reviewer} — which option works best for you?
```

### 6.2 Disagreement Anti-Patterns

| Anti-Pattern | Why It Fails | Instead |
|-------------|-------------|---------|
| "I disagree" with no explanation | Dismissive, creates friction | Always provide evidence |
| Silently applying a change you disagree with | Resentment, technical debt | Explain your concern, then comply if overruled |
| "I'll fix it later" without creating a tracking issue | It never gets fixed | Create the issue now, link it in the response |
| Arguing beyond 2 rounds in PR comments | Wastes everyone's time, blocks the PR | Escalate per protocol above |
| Citing authority ("I'm more senior") | Toxic, irrelevant to code quality | Argue with evidence, not credentials |
| Making changes without telling the reviewer | Breaks trust, reviewer cannot track | Always reply before or after making changes |

---

