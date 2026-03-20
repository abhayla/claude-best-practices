# MODE 2: COMPOSE POST / COMMENT

### Post Rules

- **Title:** 100-200 chars ideal (max 300). Clear, specific, not clickbait.
- **Body:** 200-800 words for text posts. Use markdown formatting.
- **Tone:** Match the subreddit culture (technical for r/programming, casual for r/gaming).
- **No self-promotion** unless the subreddit explicitly allows it (check rules first).
- Always show word count and reading time estimate.

### Title Formulas (proven high-engagement patterns)

| Type | Formula | Example |
|------|---------|---------|
| Question | "[Specific question] + [context]?" | "How do you handle database migrations in production without downtime?" |
| Show & Tell | "I built [thing] — [key result/stat]" | "I built a CLI tool that reduced our deploy time by 80%" |
| Discussion | "[Observation/opinion] — [invitation to discuss]" | "After 10 years of Python, I switched to Rust — here are my honest thoughts" |
| Resource | "[Descriptive title] — [what makes it useful]" | "A visual guide to CSS Grid — finally one that made sense to me" |
| Help Request | "[Technology]: [specific problem] when [context]" | "PostgreSQL: Connection pool exhaustion when running parallel migrations" |

### Comment Rules

- **Length:** 2-6 sentences for most comments. Longer for detailed answers.
- **Structure:** Lead with the answer, then explain. Don't bury the lede.
- **Add value:** Share experience, provide sources, offer alternatives.
- **No empty agreement** — "This!" or "+1" adds nothing.
- **Quote the part you're responding to** using `>` for clarity in long threads.

### Subreddit Compliance Check

Before composing, verify:
1. Fetch subreddit rules: `https://www.reddit.com/r/SUBREDDIT/about/rules.json`
2. Check posting requirements (flair, minimum karma, account age)
3. Review recent top posts for tone and format patterns
4. Identify banned topics or formats

### AI-Tell Detection & Humanization

Avoid these AI-sounding patterns that get downvoted on Reddit:

| AI Tell | Human Alternative |
|---------|-------------------|
| "Absolutely!" / "Great question!" | Just answer directly |
| "Here's the thing..." | Drop the filler, state the point |
| "It's worth noting that..." | Just note it |
| "Let me break this down..." | Just break it down |
| "In my experience..." (when AI has none) | Cite a source instead |
| Bullet-point everything | Use flowing paragraphs for discussion |
| Perfect grammar + formal tone | Match the subreddit's casual level |
| "I hope this helps!" | Omit — the help speaks for itself |
| Numbered lists for everything | Use prose with natural transitions |
| "That being said..." / "Having said that..." | Cut the transition, just state the next point |

### Output Format

```
SUBREDDIT: r/[name]
TYPE: [text post / link post / comment / reply]
FLAIR: [if required]

TITLE: [title text]
CHARS: X/300

BODY:
[content in markdown]

WORDS: X | READING TIME: ~Xm
COMPLIANCE: [rules checked ✓ / issues flagged ⚠]
```

---

