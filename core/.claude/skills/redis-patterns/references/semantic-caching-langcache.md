# Semantic Caching (LangCache)

## Semantic Caching (LangCache)

> LangCache is currently in preview on Redis Cloud.

```python
from langcache import LangCache

lang_cache = LangCache(
    server_url=f"https://{os.getenv('HOST')}",
    cache_id=os.getenv("CACHE_ID"),
    api_key=os.getenv("API_KEY")
)

result = lang_cache.search(prompt="What is Redis?", similarity_threshold=0.9)
if result:
    response = result[0]["response"]
else:
    response = llm.generate("What is Redis?")
    lang_cache.set(prompt="What is Redis?", response=response)
```

**Best practices:** Start threshold at 0.9. Use separate cache IDs for different LLM tasks. Use custom attributes for filtering within a cache.

