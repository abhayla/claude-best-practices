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
version: "1.0.1"
type: workflow
---

# Twitter/X Comprehensive Skill

**Request:** $ARGUMENTS

---

Determine which mode to use based on the user's request, then follow that section.

---

## STEP 1: Read Post

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

## STEP 2: Compose Tweet

Craft an optimized tweet or thread. Apply these rules:


**Read:** `references/compose-tweet.md` for detailed step 2: compose tweet reference material.

## STEP 3: Viral Potential Scoring

Score a tweet's viral potential using the 19-element system based on X's open-source recommendation algorithm.


**Read:** `references/viral-potential-scoring.md` for detailed step 3: viral potential scoring reference material.

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

## STEP 4: Search & Discover

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

## STEP 5: Post & Engage

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

## STEP 6: Follower & Social Management

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

## STEP 7: Account Health & Growth


**Read:** `references/account-health-growth.md` for detailed step 7: account health & growth reference material.

## STEP 8: Keyword Monitoring

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

## STEP 9: Content Strategy & Planning

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
