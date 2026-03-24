---
name: reddit
description: >
  Manage Reddit interactions: read posts and threads, compose posts and comments, analyze
  sentiment and consensus, post via API, search and discover, score viral potential, monitor
  keywords and subreddits, plan content strategy, and moderate communities. Use when
  interacting with Reddit for reading, posting, analyzing, or monitoring.
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
allowed-tools: "Bash Read Write Grep Glob WebFetch WebSearch Agent"
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

## MODE 2: COMPOSE POST / COMMENT

Craft an optimized Reddit post or comment. Reddit has very different norms from Twitter — longer form, community-specific, anti-self-promotion.


**Read:** `references/mode-2-compose-post-comment.md` for detailed mode 2: compose post / comment reference material.

## MODE 3: THREAD ANALYSIS

Analyze a Reddit thread for sentiment, consensus, key arguments, and discussion quality.


**Read:** `references/mode-3-thread-analysis.md` for detailed mode 3: thread analysis reference material.

## Thread Analysis: "[Post Title]"
Subreddit: r/[name] | Comments: X | Score: X | Upvote Ratio: X%


**Read:** `references/thread-analysis-post-title.md` for detailed thread analysis: "[post title]" reference material.

## MODE 4: VIRAL POTENTIAL SCORING

Score a Reddit post's viral potential using a 15-element system based on Reddit's ranking algorithm and community dynamics.


**Read:** `references/mode-4-viral-potential-scoring.md` for detailed mode 4: viral potential scoring reference material.

## Score: XX/100 (Grade: X)


**Read:** `references/score-xx100-grade-x.md` for detailed score: xx/100 (grade: x) reference material.

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


**Read:** `references/mode-6-post-engage.md` for detailed mode 6: post & engage reference material.

# Comment on a post (thing_id = t3_POST_ID)
# Reply to a comment (thing_id = t1_COMMENT_ID)
curl -s -X POST "https://oauth.reddit.com/api/comment" \
  -H "Authorization: Bearer $TOKEN" -H "User-Agent: ClaudeCode/1.0" \
  -d "thing_id=THING_ID&text=COMMENT_MARKDOWN"
```

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


**Read:** `references/reddit-monitor-keyword.md` for detailed reddit monitor: "keyword" reference material.

# Compare mention volume
for TERM in "my-product" "competitor-a" "competitor-b"; do
  echo "$TERM:"
  curl -s -H "User-Agent: ClaudeCode/1.0" \
    "https://www.reddit.com/search.json?q=$TERM&sort=new&t=month&limit=100" \
    | jq '.data.children | length'
  sleep 2
done
```

## MODE 9: CONTENT STRATEGY & PLANNING

Generate a content plan optimized for Reddit's unique dynamics.


**Read:** `references/mode-9-content-strategy-planning.md` for detailed mode 9: content strategy & planning reference material.

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

