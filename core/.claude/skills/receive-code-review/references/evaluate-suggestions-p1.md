# STEP 3: Evaluate Suggestions (P1)

### 3.1 Decision Framework

For each suggestion, evaluate:

| Factor | Question |
|--------|----------|
| **Correctness** | Is the suggested approach more correct than the current one? |
| **Consistency** | Does the suggestion match existing patterns in this codebase? |
| **Complexity** | Does the suggestion simplify or complicate the code? |
| **Scope** | Is the suggestion within the scope of this PR, or should it be a follow-up? |
| **Trade-offs** | What does the suggestion gain and what does it cost? |

### 3.2 Accept a Suggestion

When the suggestion improves the code:

```
Good point — updated to {approach}. See {commit_sha}.

{Optional: brief note on how you adapted the suggestion if it was not applied exactly as proposed.}
```

**Example:**
```
Good point — updated to use a dataclass instead of the raw dict. This also let
me drop the manual validation since dataclass fields handle type checking. See
a1b2c3d.
```

### 3.3 Decline a Suggestion

When you disagree with the suggestion, always explain with evidence:

```
Considered this — keeping the current approach because {reason}.

{Evidence supporting your decision: benchmarks, documentation links, precedent
in the codebase, or constraints the reviewer may not be aware of.}

{If applicable: "Happy to discuss further or try a different approach if you
feel strongly about this."}
```

**Example — declining with benchmarks:**
```
Considered this — keeping the current approach because the HashMap lookup is
O(1) amortized and this function is called ~10K times per request in our hot
path. The BTreeMap suggestion would give us sorted iteration (which we don't
need here) at the cost of O(log n) lookups.

Benchmark results on the target dataset:
  HashMap: 1.2ms avg
  BTreeMap: 3.8ms avg

Happy to discuss further if there is a correctness concern I am missing.
```

**Example — declining with scope:**
```
Agreed this would be a good improvement, but it touches the serialization layer
which is shared with 3 other endpoints. I would prefer to handle this in a
follow-up PR to keep this change focused.

Created issue #456 to track the refactor.
```

### 3.4 Adapt a Suggestion

When the reviewer's direction is right but the specific approach needs adjustment:

```
Agreed with the direction — went with a slightly different approach: {what you
did instead}. The reviewer suggested {their approach}, but {reason for
adaptation}. See {commit_sha}.
```

---

