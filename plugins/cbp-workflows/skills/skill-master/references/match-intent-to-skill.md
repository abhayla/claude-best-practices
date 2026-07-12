# STEP 4: Match Intent to Skill

### 4.1 Scoring Algorithm

For each skill in the catalog, calculate a match score:

| Signal | Points | How to Detect |
|--------|--------|---------------|
| Exact trigger match | 100 | User input exactly matches a trigger string from frontmatter |
| Slash command match | 90 | User typed `/<name>` and it matches a skill name |
| Trigger substring match | 60 | A trigger from frontmatter appears as a substring in the user's input |
| Description keyword match | 40 | 2+ key phrases from user input appear in the skill's description |
| Single keyword match | 20 | 1 key phrase from user input appears in the skill's description |
| Stack prefix match | 30 | User mentions a technology and a skill has the matching stack prefix |
| Category alignment | 10 | User's action verb maps to the skill's inferred category |

Sum the points for each skill. Rank by total score descending.

### 4.2 Present Results

Based on the scoring results:

| Scenario | Action |
|----------|--------|
| Top skill scores >= 80 and is 20+ points ahead of #2 | **Strong match** — Route directly. Present: "Routing to `/skill-name` — {description}. Invoke now? (Y/n)" |
| Top 2-3 skills score >= 40 with < 20 point spread | **Ambiguous match** — Present top 3 with scores and let user pick |
| No skill scores >= 40 | **No match** — Go to Step 4.3 |

#### Strong Match Example

```
MATCH FOUND (confidence: high)
  Skill: /systematic-debugging
  Description: Structured debugging methodology with hypothesis testing
  Match reason: Your request mentions "debug" and "failing test" — exact trigger match

  Invoke /systematic-debugging now? (Y/n)
```

#### Ambiguous Match Example

```
MULTIPLE MATCHES — please pick one:

  1. /implement (score: 65)
     Implement a feature or fix following a structured workflow
     Match: "build" keyword in your request matches description

  2. /executing-plans (score: 55)
     Execute tasks from a pre-written plan
     Match: "build" keyword, but requires a plan as input

  3. /brainstorm (score: 45)
     Explore approaches before committing to implementation
     Match: "feature" keyword in your request

  Which skill? (1/2/3 or describe your task in more detail)
```

### 4.3 Handle No Match

When no skill scores above the threshold:

1. Show the closest match (highest score even if below threshold) with an explanation of the gap:
   ```
   CLOSEST MATCH (low confidence):
     Skill: /implement (score: 25)
     Gap: Your request mentions "refactor database schema" but no skill
          specifically handles schema refactoring.
   ```

2. Suggest alternatives:
   ```
   SUGGESTIONS:
     - Rephrase your request with different keywords
     - Use /writing-skills to create a new skill for this task
     - Use /brainstorm to explore the problem space first
     - Browse the full catalog: /skill-master list
   ```

3. Offer a keyword-based search across all skill descriptions:
   ```
   SEARCH RESULTS for "database schema":
     /fastapi-db-migrate  — mentions "database" and "migration" in description
     /pg-query            — mentions "database" and "query" in description
   ```

### 4.4 Route to Selected Skill

Once the user confirms (or the match is strong enough for auto-routing):

1. Read the full SKILL.md content of the selected skill (not just frontmatter)
2. Invoke the skill using the Skill tool:
   ```
   Skill("<skill-name>", args="<user's original request>")
   ```
3. Record the invocation in session state (Step 7)

---

