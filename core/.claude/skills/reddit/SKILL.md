---
name: reddit
description: >
  Comprehensive Reddit skill: read posts & threads, compose posts & comments, analyze threads
  (sentiment, consensus, arguments), post via API, search & discover, engage (upvote/comment/reply),
  score viral potential (15-element system), monitor keywords & subreddits, manage karma & account
  health, plan content strategy, and moderate communities. Supports multiple access methods:
  WebFetch, Reddit API (OAuth2), Gemini CLI fallback, and MCP integration.
  Use when user wants to interact with Reddit in any way.
triggers:
  - reddit.com
  - subreddit
  - reddit post
  - reddit comment
  - post to reddit
  - reddit search
  - reddit monitor
  - reddit strategy
  - reddit karma
  - reddit analytics
  - reddit thread
  - reddit analysis
  - reddit growth
  - reddit viral
  - reddit moderation
  - compose reddit
  - reddit engagement
argument-hint: "<action> [options] — e.g., 'read https://reddit.com/r/...', 'compose post about AI for r/programming', 'analyze thread https://...', 'search r/python for async patterns', 'monitor r/startups for my-product'"
version: "1.0.0"
type: reference
allowed-tools: "Bash Read Write Edit Grep Glob WebFetch WebSearch Agent"
---

# Reddit Comprehensive Skill

**Request:** $ARGUMENTS

---

Determine which mode to use based on the user's request, then follow that section.

---

## MODE 1: READ POST / THREAD

Fetch any Reddit post, comment thread, or user profile as structured data.

### Option A: Reddit JSON API (no auth required)

Append `.json` to any Reddit URL:

```bash
# Read a post + comments
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/comments/POST_ID/SLUG.json"

# Read a subreddit feed (hot/new/rising/top)
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/hot.json?limit=25"

# Read user profile
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/user/USERNAME/about.json"

# Read user's posts or comments
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/user/USERNAME/submitted.json?limit=25"
```

**Response schema (post):**
```json
{
  "data": {
    "title": "Post title",
    "selftext": "Post body (markdown)",
    "author": "username",
    "subreddit": "subreddit_name",
    "score": 1234,
    "upvote_ratio": 0.95,
    "num_comments": 56,
    "created_utc": 1709856000,
    "url": "link or self URL",
    "link_flair_text": "Discussion",
    "is_self": true
  }
}
```

### Option B: WebFetch (may get 403 — use Option A or C as fallback)

```
WebFetch: https://www.reddit.com/r/SUBREDDIT/comments/POST_ID/SLUG
```

### Option C: Gemini CLI Fallback (when Reddit blocks requests)

Use when Options A and B both fail with 403/blocked errors:

```bash
# Pick a unique session name
SESSION="gemini_reddit_$(date +%s)"
tmux new-session -d -s $SESSION -x 200 -y 50
tmux send-keys -t $SESSION 'gemini -m gemini-3-pro-preview' Enter
sleep 3

# Send the Reddit query
tmux send-keys -t $SESSION 'Fetch and summarize this Reddit thread: URL_HERE' Enter
sleep 30
tmux capture-pane -t $SESSION -p -S -500

# Cleanup
tmux kill-session -t $SESSION
```

### Option D: old.reddit.com (lighter pages, easier to parse)

```bash
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://old.reddit.com/r/SUBREDDIT/comments/POST_ID/SLUG"
```

After fetching, do whatever the user asked: summarize, extract key points, analyze arguments, etc.

---

## MODE 2: COMPOSE POST / COMMENT

Craft an optimized Reddit post or comment. Reddit has very different norms from Twitter — longer form, community-specific, anti-self-promotion.

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

## MODE 3: THREAD ANALYSIS

Analyze a Reddit thread for sentiment, consensus, key arguments, and discussion quality.

### Analysis Process

1. **Fetch the thread** using Mode 1 (include comments: `?limit=500&depth=10`)
2. **Parse comment tree** — map parent-child relationships, scores, and authors
3. **Run analysis** on each dimension below

### Analysis Dimensions

#### Sentiment Breakdown
| Category | Description |
|----------|-------------|
| Positive | Supportive, enthusiastic, agreeing |
| Negative | Critical, opposing, frustrated |
| Neutral | Informational, factual, asking questions |
| Mixed | Contains both positive and negative elements |

Report percentages for each category.

#### Argument Extraction
- **Top 3-5 arguments FOR** the topic (with scores and representative quotes)
- **Top 3-5 arguments AGAINST** the topic (with scores and representative quotes)
- **Most cited sources/evidence** across the thread
- **Novel arguments** (unique points not commonly made)

#### Consensus & Controversy
- **Consensus points:** Where most commenters agree (high-score comments with few rebuttals)
- **Controversial points:** Where the community is divided (comments with many replies and mixed scores)
- **Minority opinions:** Downvoted comments that still present valid arguments

#### Discussion Quality Rating
| Factor | Rating | Description |
|--------|--------|-------------|
| Depth | 1-5 | Are arguments substantive with evidence? |
| Civility | 1-5 | Is discussion respectful or hostile? |
| Diversity | 1-5 | Are multiple viewpoints represented? |
| Expertise | 1-5 | Do commenters show domain knowledge? |
| Signal/Noise | 1-5 | Ratio of substantive to low-effort comments |

### Output Format

```
## Thread Analysis: "[Post Title]"
Subreddit: r/[name] | Comments: X | Score: X | Upvote Ratio: X%

### Executive Summary
[2-3 sentence summary of the overall discussion]

### Sentiment Distribution
Positive: X% | Negative: X% | Neutral: X% | Mixed: X%

### Key Arguments

**FOR:**
1. [Argument] (Score: X, Quoted: "...")
2. ...

**AGAINST:**
1. [Argument] (Score: X, Quoted: "...")
2. ...

### Consensus Points
- [Point where most commenters agree]
- ...

### Controversial Topics
- [Divisive issue] — [brief description of both sides]
- ...

### Discussion Quality
| Factor | Score | Notes |
|--------|-------|-------|
| Depth | X/5 | ... |
| Civility | X/5 | ... |
| Diversity | X/5 | ... |
| Expertise | X/5 | ... |
| Signal/Noise | X/5 | ... |
**Overall: X/25**

### Notable Quotes
> "[Most insightful comment]" — u/username (X points)
> "[Most controversial comment]" — u/username (X points)
```

---

## MODE 4: VIRAL POTENTIAL SCORING

Score a Reddit post's viral potential using a 15-element system based on Reddit's ranking algorithm and community dynamics.

### Tier 1: Core Engagement (50 points)

| Factor | Max | High | Medium | Low |
|--------|-----|------|--------|-----|
| Upvote Potential | 15 | Broadly relatable, emotionally resonant | Interesting to subreddit regulars | Niche or already-discussed |
| Comment Potential | 15 | Invites debate, asks question, divisive opinion | Interesting enough to discuss | Statement with no hook |
| Share/Crosspost Potential | 10 | Relevant to multiple subreddits, link-worthy | Useful within its niche | Subreddit-specific only |
| Save Potential | 10 | Reference-worthy guide, tool, or resource | Somewhat useful for later | No lasting value |

### Tier 2: Content Quality (30 points)

| Factor | Max | Description |
|--------|-----|-------------|
| Title Strength | 8 | Clear, specific, curiosity-inducing without clickbait |
| Body Quality | 7 | Well-structured, formatted, right length for subreddit |
| Originality | 5 | Novel perspective, OC, not a repost |
| Evidence/Sources | 5 | Data, links, screenshots, personal experience |
| Formatting | 5 | Headers, code blocks, lists used appropriately |

### Tier 3: Community Fit (20 points)

| Factor | Max | Description |
|--------|-----|-------------|
| Subreddit Relevance | 6 | Matches the subreddit's core topic and norms |
| Timing | 5 | Posted during peak hours for the subreddit |
| Flair Compliance | 3 | Correct flair selected (critical in strict subreddits) |
| Rule Compliance | 3 | Follows all sidebar rules |
| Author Reputation | 3 | Account age, karma, history in the subreddit |

### Penalties (subtract from total)

| Risk | Range | Trigger |
|------|-------|---------|
| Spam Detection | -10 to -30 | Self-promotion, affiliate links, repetitive posting |
| Rule Violation | -10 to -25 | Breaks subreddit rules (auto-removed) |
| Repost | -5 to -15 | Content previously posted in the subreddit |
| AI-Tell Detection | -5 to -15 | Obviously AI-generated content patterns |
| Clickbait Title | -5 to -10 | Title overpromises or misleads |

### Grade Scale

| Score | Grade | Verdict |
|-------|-------|---------|
| 90-100 | S | Front page potential |
| 75-89 | A | Strong — likely to gain traction |
| 60-74 | B | Good — solid engagement expected |
| 45-59 | C | Average — consider improvements |
| 30-44 | D | Below average — needs rework |
| 0-29 | F | Low potential — rewrite recommended |

### Scoring Output Format

```
## Score: XX/100 (Grade: X)

### Breakdown
| Factor | Score | Notes |
|--------|-------|-------|
| Upvote Potential | X/15 | ... |
| Comment Potential | X/15 | ... |
| ... | ... | ... |

### Penalties Applied
(if any)

### Top 3 Improvements
1. [Specific actionable improvement]
2. [Specific actionable improvement]
3. [Specific actionable improvement]

### Optimized Version
[Rewritten title and opening paragraph applying the improvements]
```

---

## MODE 5: SEARCH & DISCOVER

Search Reddit for posts, subreddits, and users.

### Reddit JSON Search (no auth required)

```bash
# Search within a subreddit
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/search.json?q=QUERY&restrict_sr=on&sort=relevance&t=all&limit=25"

# Search all of Reddit
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/search.json?q=QUERY&sort=relevance&t=all&limit=25"

# Sort options: relevance, hot, top, new, comments
# Time filters (t=): hour, day, week, month, year, all
```

### OAuth API Search (authenticated — more results, higher rate limits)

```bash
# Get OAuth token
TOKEN=$(curl -s -X POST "https://www.reddit.com/api/v1/access_token" \
  -u "$REDDIT_CLIENT_ID:$REDDIT_CLIENT_SECRET" \
  -d "grant_type=password&username=$REDDIT_USERNAME&password=$REDDIT_PASSWORD" \
  -H "User-Agent: ClaudeCode/1.0" | jq -r '.access_token')

# Search with OAuth
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/r/SUBREDDIT/search?q=QUERY&restrict_sr=on&sort=top&t=month&limit=100"
```

### Advanced Search Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `AND` / `OR` | `python AND async` | Boolean logic |
| `NOT` / `-` | `python NOT java` | Exclude terms |
| `""` | `"error handling"` | Exact phrase |
| `author:` | `author:username` | Posts by specific user |
| `subreddit:` | `subreddit:python` | Within specific subreddit |
| `site:` | `site:github.com` | Links to specific domain |
| `selftext:` | `selftext:tutorial` | Search post body only |
| `title:` | `title:beginner` | Search titles only |
| `flair:` | `flair:Discussion` | Filter by flair |
| `self:yes/no` | `self:yes` | Text posts only / link posts only |
| `nsfw:no` | `nsfw:no` | Exclude NSFW content |

### Subreddit Discovery

```bash
# Find related subreddits
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/subreddits/search.json?q=TOPIC&limit=25"

# Get subreddit info
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/about.json"

# Subreddit rules
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/about/rules.json"
```

### Analysis After Search

- Sort results by engagement metrics (score, num_comments, upvote_ratio)
- Identify top-performing content patterns in the subreddit
- Extract common title formats, post lengths, and flair usage
- Generate a content opportunity report

---

## MODE 6: POST & ENGAGE

Post, comment, reply, and interact on Reddit. **Requires OAuth credentials.**

### Environment Variables Required

```
REDDIT_CLIENT_ID      — OAuth app client ID
REDDIT_CLIENT_SECRET  — OAuth app client secret
REDDIT_USERNAME       — Reddit username
REDDIT_PASSWORD       — Reddit password
```

### Authentication

```bash
TOKEN=$(curl -s -X POST "https://www.reddit.com/api/v1/access_token" \
  -u "$REDDIT_CLIENT_ID:$REDDIT_CLIENT_SECRET" \
  -d "grant_type=password&username=$REDDIT_USERNAME&password=$REDDIT_PASSWORD" \
  -H "User-Agent: ClaudeCode/1.0" | jq -r '.access_token')
```

### Submit a Text Post

```bash
curl -s -X POST "https://oauth.reddit.com/api/submit" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "kind=self&sr=SUBREDDIT&title=TITLE&text=BODY_MARKDOWN&flair_id=FLAIR_ID"
```

### Submit a Link Post

```bash
curl -s -X POST "https://oauth.reddit.com/api/submit" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "kind=link&sr=SUBREDDIT&title=TITLE&url=URL"
```

### Comment / Reply

```bash
# Comment on a post (thing_id = t3_POST_ID)
# Reply to a comment (thing_id = t1_COMMENT_ID)
curl -s -X POST "https://oauth.reddit.com/api/comment" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "thing_id=THING_ID&text=COMMENT_MARKDOWN"
```

### Engagement Actions

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| Upvote | POST | `/api/vote` | `id=THING_ID&dir=1` |
| Downvote | POST | `/api/vote` | `id=THING_ID&dir=-1` |
| Unvote | POST | `/api/vote` | `id=THING_ID&dir=0` |
| Save | POST | `/api/save` | `id=THING_ID` |
| Unsave | POST | `/api/unsave` | `id=THING_ID` |
| Edit | POST | `/api/editusertext` | `thing_id=THING_ID&text=NEW_TEXT` |
| Delete | POST | `/api/del` | `id=THING_ID` |
| Hide | POST | `/api/hide` | `id=THING_ID` |
| Report | POST | `/api/report` | `thing_id=THING_ID&reason=REASON` |
| Crosspost | POST | `/api/submit` | `kind=crosspost&sr=TARGET_SR&crosspost_fullname=t3_POST_ID&title=TITLE` |

### Set Post Flair

```bash
# Get available flairs
curl -s "https://oauth.reddit.com/r/SUBREDDIT/api/link_flair_v2" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0"

# Apply flair
curl -s -X POST "https://oauth.reddit.com/r/SUBREDDIT/api/selectflair" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "link=t3_POST_ID&flair_template_id=FLAIR_ID"
```

### Send Private Message

```bash
curl -s -X POST "https://oauth.reddit.com/api/compose" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "to=USERNAME&subject=SUBJECT&text=MESSAGE_MARKDOWN"
```

### Rate Limits

| Scope | Limit |
|-------|-------|
| OAuth API (authenticated) | 100 requests / 60 seconds |
| Public JSON API (unauthenticated) | 10 requests / 60 seconds |
| Post submission | ~1 post / 10 minutes (new accounts stricter) |
| Comments | Rate-limited dynamically based on karma in subreddit |

**Always add 2-4 second delays between write operations.**

### Thing ID Prefixes

| Prefix | Type |
|--------|------|
| `t1_` | Comment |
| `t2_` | Account |
| `t3_` | Post/Link |
| `t4_` | Message |
| `t5_` | Subreddit |

---

## MODE 7: KARMA & ACCOUNT HEALTH

Analyze and grow Reddit account health.

### Account Stats

```bash
# Get account info
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/api/v1/me"

# Get karma breakdown by subreddit
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/api/v1/me/karma"
```

### Account Health Score (0-100)

| Factor | Weight | Healthy | Warning | Critical |
|--------|--------|---------|---------|----------|
| Account Age | 15% | >1 year | 3-12 months | <3 months |
| Comment Karma | 20% | >5000 | 500-5000 | <500 |
| Post Karma | 15% | >2000 | 200-2000 | <200 |
| Karma Diversity | 15% | Active in 10+ subs | 3-10 subs | 1-2 subs |
| Comment/Post Ratio | 10% | 3:1 to 10:1 | 1:1 to 3:1 | <1:1 or >20:1 |
| Engagement Rate | 15% | >5 avg score | 2-5 avg score | <2 avg score |
| Posting Frequency | 10% | 3-7x/week | 1-2x/week or 8-14x/week | <1x/month or >20x/day |

### Karma Building Strategy

**Phase 1: New Account (0-500 karma)**
- Comment on rising posts in large subreddits (r/AskReddit, r/todayilearned)
- Sort by "rising" — these posts have the most growth potential
- Write genuine, helpful, or funny comments (2-4 sentences)
- **Avoid:** Posting links, self-promotion, or anything that looks automated

**Phase 2: Established (500-5000 karma)**
- Start posting original content in niche subreddits
- Answer questions in your expertise area (r/learnprogramming, r/webdev, etc.)
- Engage in discussions — replies to your comments boost your visibility
- **Avoid:** Karma farming subreddits (looks suspicious to mods)

**Phase 3: Trusted (5000+ karma)**
- Share original projects, write-ups, and resources
- Cross-post to relevant communities
- Your posts are less likely to be auto-filtered by spam detection
- Consider contributing to subreddit wikis

### Spam Filter Avoidance

Words/patterns that trigger Reddit's spam filter:
- "Check out my..." / "I just launched..." (in title)
- Shortened URLs (bit.ly, t.co, etc.)
- Affiliate links or referral codes
- Multiple exclamation marks / ALL CAPS titles
- Posting the same link to multiple subreddits simultaneously
- New account + link post = almost always filtered

### Shadowban Detection

```bash
# Check if posts appear publicly
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/user/USERNAME/about.json"
# If 404 → account may be shadowbanned

# Check a specific post's visibility
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/new.json?limit=100" | jq '.data.children[].data.author' | grep USERNAME
# If your post doesn't appear → it may be filtered
```

---

## MODE 8: KEYWORD & SUBREDDIT MONITORING

Track keywords, brand mentions, competitors, or topics across subreddits.

### Real-Time Monitoring

```bash
# Monitor new posts mentioning a keyword
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/search.json?q=KEYWORD&sort=new&t=hour&limit=25"

# Monitor a subreddit's new posts
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/new.json?limit=25"

# Monitor comments mentioning a keyword (via Pushshift alternative / search)
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/search.json?q=KEYWORD&type=comment&sort=new&t=day&limit=50"
```

### Monitoring Report Format

```
## Reddit Monitor: "KEYWORD"
Period: [date range]
Subreddits tracked: [list]
Total mentions: X (Posts: X, Comments: X)

### Sentiment Summary
Positive: X% | Negative: X% | Neutral: X%

### Top Posts Mentioning Keyword (by engagement)
1. r/subreddit — "[title]" (Score: X, Comments: X)
   Context: [brief summary of how keyword was mentioned]
2. ...

### Emerging Trends
- [New theme or pattern in discussions]
- [Sentiment shift compared to previous period]

### Volume Trend
[increasing / stable / decreasing] vs. previous period

### Notable Mentions
> "Direct quote mentioning keyword" — u/user in r/subreddit (X points)

### Recommended Actions
- [Reply to high-engagement thread about X]
- [Create a post addressing common question Y]
- [Monitor emerging subreddit r/Z where topic is gaining traction]
```

### Competitor Monitoring

Track competitor mentions alongside your own:

```bash
# Compare mention volume
for TERM in "my-product" "competitor-a" "competitor-b"; do
  echo "$TERM:"
  curl -s -H "User-Agent: ClaudeCode/1.0" \
    "https://www.reddit.com/search.json?q=$TERM&sort=new&t=month&limit=100" \
    | jq '.data.children | length'
  sleep 2
done
```

### Alert Criteria

Flag mentions that need immediate attention:
- **Negative sentiment** about your product/brand
- **Feature requests** or **bug reports** in the wild
- **Comparison threads** where your product is discussed vs. competitors
- **High-engagement posts** (>50 upvotes) mentioning your keywords

---

## MODE 9: CONTENT STRATEGY & PLANNING

Generate a content plan optimized for Reddit's unique dynamics.

### Reddit Content Strategy Principles

1. **Value first, promotion never** — Reddit punishes overt self-promotion
2. **Community over broadcast** — Engage in conversations, don't just post
3. **Each subreddit is its own world** — Tone, rules, and culture vary dramatically
4. **Karma is earned through genuine contribution** — No shortcuts

### Optimal Posting Times (general — verify for specific subreddits)

| Day | Best Times (US Eastern) | Why |
|-----|------------------------|-----|
| Monday | 6-8 AM, 12-2 PM | Workday browsing peaks |
| Tuesday | 7-9 AM, 1-3 PM | Highest overall engagement day |
| Wednesday | 7-9 AM, 12-2 PM | Mid-week browsing peak |
| Thursday | 7-9 AM, 12-2 PM | Consistent mid-week engagement |
| Friday | 8-10 AM | Morning browsing, drops in afternoon |
| Saturday | 8-11 AM | Casual weekend browsing |
| Sunday | 9 AM-12 PM | Pre-week planning, catching up |

**Key insight:** Post 2-3 hours before peak to catch the upvote wave as users arrive.

### Weekly Content Plan Template

| Day | Activity | Time Investment |
|-----|----------|----------------|
| Mon | Comment on 5-10 rising posts in target subreddits | 30 min |
| Tue | Post original content (text post, guide, or resource) | 45 min |
| Wed | Answer questions in help/discussion subreddits | 30 min |
| Thu | Engage with replies to your posts/comments | 20 min |
| Fri | Share interesting link with substantial commentary | 30 min |
| Sat | Participate in weekend threads / casual discussions | 20 min |
| Sun | Plan next week's content, research trending topics | 30 min |

### Content Type Effectiveness by Subreddit Size

| Subreddit Size | Best Content Types | Why |
|----------------|-------------------|-----|
| <10K subs | Niche expertise, detailed guides | Small community values depth |
| 10K-100K subs | Discussions, how-tos, OC | Active enough for engagement, not drowned out |
| 100K-1M subs | Eye-catching OC, relatable stories | Competition for attention is high |
| >1M subs | Broad appeal, humor, simple insights | Lowest common denominator wins |

### Subreddit Calibration

Before posting in a new subreddit, analyze:

```bash
# Top posts of all time — understand what succeeds
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/top.json?t=all&limit=25"

# Current hot posts — understand what's trending now
curl -s -H "User-Agent: ClaudeCode/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/hot.json?limit=25"
```

Extract patterns for:
- Average title length and format
- Post type distribution (text vs. link vs. image)
- Common flairs and topics
- Posting frequency of top contributors
- Comment depth and discussion style

### Cross-Subreddit Strategy

When sharing content across multiple subreddits:
- **Stagger posts** by 24-48 hours — never post the same thing to 5 subreddits at once
- **Customize title and body** for each subreddit's norms
- **Avoid identical cross-posts** — Reddit's spam filter flags this
- **Prioritize** the most relevant subreddit first, then expand

### Content Repurposing for Reddit

| Source | Reddit Format |
|--------|--------------|
| Blog post | Summarize key points as a text post, link to full article in body |
| GitHub project | "Show Reddit" style post with problem-solution narrative |
| YouTube video | Text summary with key timestamps, video link in body (not title) |
| Tweet thread | Expand into a detailed text post with more context |
| Newsletter | Extract the single best insight as a discussion starter |
| Conference talk | "I gave a talk on X — here are the key takeaways" |

---

## MODE 10: MODERATION

Manage subreddit moderation tasks. **Requires moderator permissions.**

### Moderation Actions

```bash
# Remove a post or comment
curl -s -X POST "https://oauth.reddit.com/api/remove" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "id=THING_ID&spam=false"

# Approve a post or comment
curl -s -X POST "https://oauth.reddit.com/api/approve" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "id=THING_ID"

# Distinguish a comment as moderator
curl -s -X POST "https://oauth.reddit.com/api/distinguish" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "id=THING_ID&how=yes&sticky=false"

# Sticky a post
curl -s -X POST "https://oauth.reddit.com/api/set_subreddit_sticky" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "id=t3_POST_ID&state=true&num=1"

# Lock a post or comment
curl -s -X POST "https://oauth.reddit.com/api/lock" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "id=THING_ID"

# Set suggested sort
curl -s -X POST "https://oauth.reddit.com/api/set_suggested_sort" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "id=t3_POST_ID&sort=new"
```

### User Management

```bash
# Ban a user
curl -s -X POST "https://oauth.reddit.com/r/SUBREDDIT/api/friend" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "name=USERNAME&type=banned&ban_reason=REASON&duration=DAYS&note=MOD_NOTE&ban_message=MESSAGE_TO_USER"

# Unban a user
curl -s -X POST "https://oauth.reddit.com/r/SUBREDDIT/api/unfriend" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "name=USERNAME&type=banned"

# Mute a user (from modmail)
curl -s -X POST "https://oauth.reddit.com/r/SUBREDDIT/api/friend" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "name=USERNAME&type=muted"

# Set user flair
curl -s -X POST "https://oauth.reddit.com/r/SUBREDDIT/api/selectflair" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "name=USERNAME&flair_template_id=FLAIR_ID"
```

### Moderation Queue

```bash
# Get modqueue (reported/flagged items)
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/r/SUBREDDIT/about/modqueue.json?limit=100"

# Get unmoderated items
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/r/SUBREDDIT/about/unmoderated.json?limit=100"

# Get mod log
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/r/SUBREDDIT/about/log.json?limit=100"

# Get reports
curl -s -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  "https://oauth.reddit.com/r/SUBREDDIT/about/reports.json?limit=100"
```

### AutoModerator Rule Generation

When asked to create AutoMod rules, generate valid YAML:

```yaml
# Example: Auto-remove posts with banned words
type: submission
title (includes, regex): ["spam_word", "banned_phrase"]
action: remove
action_reason: "Contains banned word: {{match}}"
comment: |
  Your post was removed because it contains a banned word.
  Please review the subreddit rules and resubmit.
```

Common AutoMod patterns:
- Minimum account age / karma requirements
- Flair enforcement (auto-remove unflaired posts)
- Domain blacklisting
- Keyword filtering with escalation (remove vs. flag for review)
- Welcome messages for first-time posters
- Scheduled recurring threads

---

## CRITICAL RULES

1. **Confirm before posting** — Always show the user what will be posted and get explicit approval before any POST/DELETE API call.
2. **Rate limit awareness** — Add 2-4 second delays between write operations. Track API usage and warn before hitting limits.
3. **No credential exposure** — Never log or display API keys, tokens, client secrets, or passwords.
4. **Respect subreddit rules** — Always check subreddit rules before composing or posting. Flag potential violations.
5. **No vote manipulation** — Never automate mass upvoting/downvoting. This violates Reddit's Content Policy and results in bans.
6. **No spam** — Never post identical content to multiple subreddits simultaneously. Stagger and customize.
7. **Disclose AI assistance** — If asked or if the subreddit requires it, note the content was AI-assisted.
8. **Score before posting** — When composing, always run the viral scoring (Mode 4) and suggest improvements before posting.
9. **Humanize content** — Always run AI-tell detection from Mode 2 before finalizing any post or comment.
10. **Thing ID prefixes matter** — Always use the correct prefix (t1_ for comments, t3_ for posts) or API calls will silently fail.

---

## QUICK REFERENCE

| User Says | Mode |
|-----------|------|
| "Read/summarize this Reddit post" + URL | Mode 1: Read |
| "Write/compose/draft a post about..." | Mode 2: Compose |
| "Analyze this Reddit thread" + URL | Mode 3: Analyze |
| "Score/rate this Reddit post" | Mode 4: Score |
| "Search Reddit for..." | Mode 5: Search |
| "Post/comment/reply/upvote..." | Mode 6: Engage |
| "Check my Reddit account / karma" | Mode 7: Health |
| "Monitor Reddit for keyword X" | Mode 8: Monitor |
| "Create a Reddit content plan" | Mode 9: Strategy |
| "Moderate / remove / ban / modqueue" | Mode 10: Moderate |
