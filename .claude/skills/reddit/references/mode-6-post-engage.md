# MODE 6: POST & ENGAGE

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
