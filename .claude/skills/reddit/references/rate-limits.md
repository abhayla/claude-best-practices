# Rate Limits

### Rate Limits

| Scope | Limit |
|-------|-------|
| OAuth API (authenticated) | 100 requests / 60 seconds |
| Public JSON API (unauthenticated) | 10 requests / 60 seconds |
| Post submission | ~1 post / 10 minutes (new accounts stricter) |
| Comments | Rate-limited dynamically based on karma in subreddit |

**Always add 2-4 second delays between write operations.**

