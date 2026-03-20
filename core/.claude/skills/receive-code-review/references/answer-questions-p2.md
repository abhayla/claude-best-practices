# STEP 4: Answer Questions (P2)

### 4.1 Question Response Guidelines

| Principle | Description |
|-----------|-------------|
| **Be specific** | Reference exact file paths, line numbers, and function names |
| **Show your reasoning** | Explain the trade-off you considered, not just the conclusion |
| **Link to evidence** | Point to docs, tests, or other code that supports your answer |
| **Acknowledge valid concerns** | If the question reveals a gap, say so and address it |
| **Keep it concise** | Answer the question asked, do not over-explain unrelated context |

### 4.2 Question Response Template

```
{Direct answer to the question.}

{Supporting evidence: code reference, documentation link, or architectural
reasoning.}

{If the question reveals a valid concern: "Good catch — I've added
{test/comment/guard} to make this clearer. See {commit_sha}."}
```

**Example — explaining a design decision:**
```
Using a custom serializer here instead of Pydantic because this endpoint
streams large responses (10K+ items) and we need incremental serialization.
Pydantic's `model_dump()` materializes the entire list in memory before
serializing.

See the benchmark in `tests/bench_serialization.py` — the custom serializer
uses ~4MB peak memory vs ~200MB for Pydantic on our production dataset.

Added a comment in the code explaining this trade-off (see a1b2c3d).
```

**Example — question reveals a gap:**
```
On timeout, the current code silently drops the connection. You are right that
this is not great — the caller has no way to distinguish between a timeout and
a successful empty response.

Added a `TimeoutError` exception with a descriptive message and a retry hint.
Also added a test for the timeout path. See a1b2c3d.
```

### 4.3 Reply via GitHub CLI

```bash
