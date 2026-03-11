---
name: twitter-x
description: >
  Comprehensive Twitter/X skill: read posts, compose tweets & threads, post via API,
  search & discover, engage (like/retweet/bookmark), analyze viral potential (19-element scoring),
  grow audience, monitor keywords, manage followers, and plan content strategy.
  Use when user wants to interact with Twitter/X in any way.
triggers:
  - x.com
  - twitter.com
  - tweet
  - thread
  - viral
  - post to x
  - post to twitter
  - twitter analytics
  - twitter strategy
  - twitter growth
  - engagement score
  - make this viral
  - compose tweet
  - twitter search
  - twitter monitor
allowed-tools: "Bash Read Write Edit Grep Glob WebFetch WebSearch Agent"
argument-hint: "<action> [options] — e.g., 'read https://x.com/user/status/123', 'compose tweet about AI', 'score my tweet', 'search AI agents', 'post Hello world'"
---

# Twitter/X Comprehensive Skill

**Request:** $ARGUMENTS

---

Determine which mode to use based on the user's request, then follow that section.

---

## MODE 1: READ POST

Fetch any X/Twitter post as structured data for analysis.

### Option A: ADHX API (no auth required)

Extract `username` and `statusId` from URL patterns:
- `x.com/{user}/status/{id}`
- `twitter.com/{user}/status/{id}`

```bash
curl -s "https://adhx.com/api/share/tweet/{username}/{statusId}"
```

**Response schema:**
```json
{
  "id": "statusId",
  "url": "original URL",
  "text": "tweet body (empty if article)",
  "author": { "name": "...", "username": "...", "avatarUrl": "..." },
  "createdAt": "timestamp",
  "engagement": { "replies": 0, "retweets": 0, "likes": 0, "views": 0 },
  "article": {
    "title": "...", "previewText": "...",
    "coverImageUrl": "...", "content": "full markdown"
  }
}
```

### Option B: Jina Reader (free, requires JINA_API_KEY)

```bash
curl -s -H "Authorization: Bearer $JINA_API_KEY" \
  "https://r.jina.ai/https://x.com/{user}/status/{id}"
```

Returns plain-text extraction including author, timestamp, text, images, and thread replies.

After fetching, do whatever the user asked: summarize, analyze, extract key points, translate, etc.

---

## MODE 2: COMPOSE TWEET

Craft an optimized tweet or thread. Apply these rules:

### Single Tweet Rules
- **Hard limit:** 280 characters
- **Target:** 200-260 chars (leaves room for engagement)
- **Structure:** Hook (first line grabs attention) + Body + CTA or open question
- **No hashtag spam** — max 2 relevant hashtags, placed at end
- Always show character count: `X/280`

### Hook Formulas (proven high-engagement openers)
| Type | Formula | Example |
|------|---------|---------|
| Transformation | "I [did X]. Here's what happened:" | "I quit my job and built an AI agent. Here's what happened:" |
| Contrarian | "Most people think [belief]. They're wrong." | "Most people think you need 10k followers to monetize. They're wrong." |
| Authority | "I've [credential]. Here's [insight]:" | "I've reviewed 500 PRs this year. Here's the #1 pattern I see:" |
| Curiosity Gap | "[Number] [things] that [surprising result]:" | "3 tweets that generated $50k in revenue:" |
| Story | "In [time], I went from [A] to [B]. Here's how:" | "In 6 months, I went from 0 to 25k followers. Here's how:" |

### Thread Rules
- **Length:** 7-15 tweets ideal, 25 max
- **Tweet 1:** Must standalone as a hook — this is 80% of the thread's success
- **Each tweet:** Self-contained thought, ends with a reason to keep reading
- **Last tweet:** CTA (follow, retweet, bookmark) + link back to tweet 1
- **Numbering:** Use X/N format (e.g., "3/12")
- Show character count per tweet

### Thread Frameworks
1. **How-To:** Step-by-step guide solving a specific problem
2. **Story:** Personal narrative with lessons learned
3. **Listicle:** Curated list of tools/tips/resources
4. **Contrarian:** Challenge conventional wisdom with evidence
5. **Case Study:** Deep-dive analysis of a real example
6. **Breakdown:** Deconstruct how something works

### Content Mix (weekly posting strategy)
| Type | % | Description |
|------|---|-------------|
| Value | 40% | Tips, tutorials, insights, how-tos |
| Engagement | 30% | Questions, polls, hot takes, debates |
| Build in Public | 20% | Progress updates, lessons, behind-the-scenes |
| Promotion | 10% | Product launches, announcements, CTAs |

### Output Format
```
TWEET: [content]
CHARS: X/280
---
(or for threads)
THREAD: [Topic]
FRAMEWORK: [Which framework]
LENGTH: X tweets

1/X: [hook tweet]
CHARS: X/280

2/X: [next tweet]
CHARS: X/280
...

STANDALONE HOOK: [Tweet 1 rephrased as standalone tweet]
```

---

## MODE 3: VIRAL POTENTIAL SCORING

Score a tweet's viral potential using the 19-element system based on X's open-source recommendation algorithm.

### Tier 1: Core Engagement (60 points)
| Factor | Max | 🟢 High | 🟡 Medium | 🔴 Low |
|--------|-----|---------|-----------|--------|
| Reply Potential | 22 | Direct question or debatable claim | Invites response | Statement only |
| Retweet Potential | 16 | Actionable insight / surprising fact | Interesting but niche | No share value |
| Favorite Potential | 12 | Emotionally resonant / personal story | Useful reference | Low appeal |
| Quote Potential | 10 | Strong opinion inviting commentary | Thought-provoking | Self-contained |

### Tier 2: Extended Engagement (25 points)
| Factor | Max | Description |
|--------|-----|-------------|
| Dwell Time | 6 | Long-form / detailed content requiring reading time |
| Continuous Dwell | 4 | Thread / story arc requiring sustained attention |
| Click Potential | 5 | Compelling link with clear CTA |
| Photo Expand | 4 | Visual storytelling with multiple images |
| Video View | 3 | Video with strong hook (>5s watch time) |
| Quoted Click | 3 | Bold claim inviting verification |

### Tier 3: Relationship Building (15 points)
| Factor | Max | Description |
|--------|-----|-------------|
| Profile Click | 5 | Creates curiosity about the author |
| Follow Potential | 4 | Demonstrates ongoing value worth following for |
| Share Potential | 2 | General cross-platform sharing value |
| Share via DM | 2 | "Send to a friend" relatability |
| Share via Copy Link | 2 | Bookmark / reference worthy |

### Penalties (subtract from total)
| Risk | Range | Trigger |
|------|-------|---------|
| Not Interested | -5 to -15 | Clickbait, irrelevant content |
| Mute Risk | -5 to -15 | Repetitive, annoying patterns |
| Block Risk | -10 to -25 | Offensive, aggressive tone |
| Report Risk | -15 to -30 | Policy violations, spam signals |

### Grade Scale
| Score | Grade | Verdict |
|-------|-------|---------|
| 90-100 | S | Exceptional — high viral probability |
| 75-89 | A | Strong — likely to perform well |
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
| Reply Potential | X/22 | ... |
| ... | ... | ... |

### Penalties Applied
(if any)

### Top 3 Improvements
1. [Specific actionable improvement]
2. [Specific actionable improvement]
3. [Specific actionable improvement]

### Optimized Version
[Rewritten tweet applying the improvements]
```

---

## MODE 4: SEARCH & DISCOVER

Search tweets, users, and trends. Requires API credentials.

### Environment Variables Required
```
X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
Optional: X_API_BEARER_TOKEN (for full-archive search)
```

### Search Commands (via Twitter API v2)

**Search recent tweets (last 7 days):**
```bash
curl -s -H "Authorization: Bearer $X_API_BEARER_TOKEN" \
  "https://api.x.com/2/tweets/search/recent?query=QUERY&max_results=100&tweet.fields=created_at,public_metrics,author_id"
```

**Search with filters:**
- `"AI agents" lang:en -is:retweet` — English original tweets only
- `"claude code" has:links min_faves:10` — With links, 10+ likes
- `from:username since:2025-01-01` — From specific user since date

**Get trending topics:**
```bash
curl -s -H "Authorization: Bearer $X_API_BEARER_TOKEN" \
  "https://api.x.com/2/trends/by/woeid/1"
```

**User lookup:**
```bash
curl -s -H "Authorization: Bearer $X_API_BEARER_TOKEN" \
  "https://api.x.com/2/users/by/username/USERNAME?user.fields=public_metrics,description,created_at"
```

### Cookie-Based Search (no API key — uses rnet)

If no API keys are available and `rnet` + browser cookies are configured:
```python
# Search via GraphQL (returns 200+ tweets per query)
python rnet_twitter.py search "keyword" --mode top --count 200
python rnet_twitter.py search "keyword" --mode latest --min_faves 50
```

### Analysis After Search
- Sort by engagement (likes, retweets, impressions, quotes)
- Identify top-performing content patterns
- Extract common hooks, formats, and topics
- Generate trend report with posting recommendations

---

## MODE 5: POST & ENGAGE

Post tweets, reply, like, retweet, and manage engagement. Requires API credentials.

### Post a Tweet
```bash
curl -s -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: OAuth ..." \
  -H "Content-Type: application/json" \
  -d '{"text": "Your tweet text here"}'
```

### Post a Thread
Post tweets sequentially, each replying to the previous:
```bash
# Tweet 1 (get the ID from response)
TWEET1_ID=$(curl -s -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: OAuth ..." \
  -d '{"text": "1/N: Thread opener"}' | jq -r '.data.id')

# Tweet 2 (reply to tweet 1)
curl -s -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: OAuth ..." \
  -d "{\"text\": \"2/N: Next point\", \"reply\": {\"in_reply_to_tweet_id\": \"$TWEET1_ID\"}}"
```

### Engagement Actions
| Action | Method | Endpoint |
|--------|--------|----------|
| Like | POST | `/2/users/:id/likes` with `{"tweet_id": "..."}` |
| Unlike | DELETE | `/2/users/:id/likes/:tweet_id` |
| Retweet | POST | `/2/users/:id/retweets` with `{"tweet_id": "..."}` |
| Unretweet | DELETE | `/2/users/:id/retweets/:tweet_id` |
| Bookmark | POST | `/2/users/:id/bookmarks` with `{"tweet_id": "..."}` |
| Reply | POST | `/2/tweets` with `{"text": "...", "reply": {"in_reply_to_tweet_id": "..."}}` |
| Quote | POST | `/2/tweets` with `{"text": "...", "quote_tweet_id": "..."}` |
| Hide reply | PUT | `/2/tweets/:id/hidden` with `{"hidden": true}` |
| Delete | DELETE | `/2/tweets/:id` |

### Post with Media
```bash
# Step 1: Upload media
MEDIA_ID=$(curl -s -X POST "https://upload.twitter.com/1.1/media/upload.json" \
  -F "media=@image.jpg" \
  -H "Authorization: OAuth ..." | jq -r '.media_id_string')

# Step 2: Post with media
curl -s -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: OAuth ..." \
  -d "{\"text\": \"Check this out\", \"media\": {\"media_ids\": [\"$MEDIA_ID\"]}}"
```

### Post with Poll
```bash
curl -s -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: OAuth ..." \
  -d '{"text": "Which is better?", "poll": {"options": ["Option A", "Option B"], "duration_minutes": 1440}}'
```

### Rate Limits
| Action | Limit |
|--------|-------|
| Post tweets | 300 / 15 min |
| Like | 1000 / 24 hr |
| Follow | 400 / 24 hr |
| DM | 1000 / 15 min |
| Search | 450 / 15 min (app), 180 / 15 min (user) |

---

## MODE 6: FOLLOWER & SOCIAL MANAGEMENT

### Follower Analysis
```bash
# Get followers
curl -s -H "Authorization: Bearer $X_API_BEARER_TOKEN" \
  "https://api.x.com/2/users/:id/followers?max_results=1000&user.fields=public_metrics,created_at"

# Get following
curl -s -H "Authorization: Bearer $X_API_BEARER_TOKEN" \
  "https://api.x.com/2/users/:id/following?max_results=1000&user.fields=public_metrics,created_at"
```

### Follow / Unfollow
```bash
# Follow
curl -s -X POST "https://api.x.com/2/users/:id/following" \
  -H "Authorization: OAuth ..." -d '{"target_user_id": "TARGET_ID"}'

# Unfollow
curl -s -X DELETE "https://api.x.com/2/users/:source_id/following/:target_id" \
  -H "Authorization: OAuth ..."
```

### Mute / Block
```bash
# Mute
curl -s -X POST "https://api.x.com/2/users/:id/muting" \
  -H "Authorization: OAuth ..." -d '{"target_user_id": "TARGET_ID"}'

# Block
curl -s -X POST "https://api.x.com/2/users/:id/blocking" \
  -H "Authorization: OAuth ..." -d '{"target_user_id": "TARGET_ID"}'
```

### Unfollow Recommendations (Growth Hygiene)
Flag accounts to unfollow based on:
- **Inactive:** No tweets in 90+ days
- **Non-engagers:** Never liked/replied to your content
- **Low-value ratio:** Following/follower ratio > 10
- **Bot indicators:** Default avatar, <5 tweets, created recently

---

## MODE 7: ACCOUNT HEALTH & GROWTH

### TweepCred Health Score
Evaluate account health on a 0-100 scale:

| Factor | Weight | How to check |
|--------|--------|-------------|
| Follower/Following ratio | 20% | Healthy: >1.0, Great: >5.0 |
| Engagement rate | 25% | (likes+replies+RTs) / followers / tweets |
| Content consistency | 15% | Regular posting cadence (4-7x/week ideal) |
| Profile completeness | 10% | Bio, avatar, banner, pinned tweet, link |
| Account age vs followers | 10% | Organic growth trajectory |
| Reply ratio | 10% | Engaging with others (>30% of activity) |
| Original content ratio | 10% | Original tweets vs retweets (>60% ideal) |

### Shadowban Detection
Check for potential shadowban indicators:
1. Search for your recent tweets — if they don't appear, possible search ban
2. Check if replies are hidden from conversations — reply deboosting
3. Verify profile appears in search results — ghost ban
4. Test: `https://x.com/search?q=from:USERNAME&f=live` — should show recent tweets

### Algorithm Weight Reference (X's open-source scoring)
| Signal | Weight | Implication |
|--------|--------|-------------|
| Reply from followed | +75 | Reply to people you follow — highest signal |
| Reply general | +27 | All replies boost visibility |
| Profile click | +12 | Curiosity-driving content wins |
| Dwell time (>2min) | +10 | Long-form and threads rewarded |
| Like | +0.5 | Likes are weak signal |
| Image/Video | +2x | Media tweets get 2x distribution |
| External link | -0.5x | Links reduce reach (put in reply instead) |

### Growth Tactics
- **Reply strategy:** Reply to 10-20 accounts in your niche daily (highest ROI)
- **Posting cadence:** 1-3 tweets/day, 1-2 threads/week
- **Best times:** 8-10am and 5-7pm in your audience's timezone
- **Link placement:** Never in main tweet — put links in first reply
- **Visual content:** Include image/video for 2x algorithm boost

---

## MODE 8: KEYWORD MONITORING

Set up ongoing monitoring for keywords, competitors, or brand mentions.

### Manual Check
```bash
curl -s -H "Authorization: Bearer $X_API_BEARER_TOKEN" \
  "https://api.x.com/2/tweets/search/recent?query=KEYWORD%20-is:retweet&max_results=100&tweet.fields=created_at,public_metrics&sort_order=relevancy"
```

### Monitoring Report Format
```
## Keyword Monitor: "KEYWORD"
Period: [date range]
Total mentions: X
Sentiment: Positive X% / Neutral X% / Negative X%

### Top Tweets (by engagement)
1. @user (XX likes, XX RTs): "tweet text..."
2. ...

### Trends
- Volume: [increasing/stable/decreasing] vs last period
- Key themes: [list emerging topics]
- Notable accounts discussing: [list]

### Recommended Actions
- [Reply to high-engagement tweets about X]
- [Create content addressing trending subtopic Y]
```

---

## MODE 9: CONTENT STRATEGY & PLANNING

Generate a content calendar or strategy plan.

### Weekly Content Template
| Day | Type | Focus |
|-----|------|-------|
| Mon | Value thread | In-depth tutorial or guide |
| Tue | Engagement tweet | Question, poll, or hot take |
| Wed | Build in public | Progress update, lesson learned |
| Thu | Value tweet | Quick tip or insight |
| Fri | Engagement tweet | Weekend discussion starter |
| Sat | Curated thread | Best resources or tools roundup |
| Sun | Light / personal | Story, reflection, or meme |

### Content Pillar Framework
Define 3-5 content pillars (topics you consistently post about):
```
Pillar 1: [Core expertise] — 40% of content
Pillar 2: [Industry insights] — 25% of content
Pillar 3: [Personal journey] — 20% of content
Pillar 4: [Community / engagement] — 15% of content
```

### Repurposing Strategy
| Source | Twitter Format |
|--------|---------------|
| Blog post | Thread (key points as tweets) |
| YouTube video | Thread summary + video link in reply |
| Podcast episode | 3-5 standalone quote tweets |
| Newsletter | Best insight as single tweet |
| GitHub release | Build-in-public announcement thread |

---

## CRITICAL RULES

1. **Character limits are sacred** — Never exceed 280 chars per tweet. Always show count.
2. **No hashtag spam** — Max 2 hashtags, at the end. Zero is often better.
3. **Links kill reach** — Put URLs in the first reply, not the main tweet.
4. **Confirm before posting** — Always show the user what will be posted and get explicit approval before any POST/DELETE API call.
5. **Rate limit awareness** — Track API usage and warn before hitting limits.
6. **No credential exposure** — Never log or display API keys, tokens, or cookies.
7. **Disclose AI authorship** — If asked, note the tweet was AI-assisted.
8. **Score before posting** — When composing, always run the viral scoring (Mode 3) and suggest improvements before the user posts.

---

## QUICK REFERENCE

| User Says | Mode |
|-----------|------|
| "Read/summarize this tweet" + URL | Mode 1: Read |
| "Write/compose/draft a tweet about..." | Mode 2: Compose |
| "Score/check/rate this tweet" | Mode 3: Score |
| "Search Twitter for..." | Mode 4: Search |
| "Post/tweet/reply/like/retweet..." | Mode 5: Post & Engage |
| "Show my followers / who to unfollow" | Mode 6: Social |
| "Check my account health / shadowban" | Mode 7: Health |
| "Monitor keyword X" | Mode 8: Monitor |
| "Create a content plan / strategy" | Mode 9: Strategy |
