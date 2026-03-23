---
name: ai-gemini-api
description: >
  Apply Google Gemini API patterns including client setup with google-genai SDK,
  structured output, prompt design, and troubleshooting. Use when integrating
  or debugging Gemini-powered features.
allowed-tools: "Read Grep Glob"
argument-hint: ""
version: "1.0.1"
type: reference
---

# Gemini API Reference

Quick-reference for Gemini API integration patterns.

---

## SDK & Client Setup

| Detail | Value |
|--------|-------|
| SDK | `google-genai` (NOT the old `google-generativeai`) |
| API key env var | `GOOGLE_AI_API_KEY` |
| Async | Uses `client.aio.models.generate_content()` — NEVER use sync methods |

```python
from google import genai

client = genai.Client(api_key=api_key)

# All generation calls MUST use client.aio (native async)
response = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=config
)
```

## Structured Output

Two schema parameters available:

| Parameter | Type | Notes |
|-----------|------|-------|
| `response_schema` | `genai.types.Schema` | Native SDK schema |
| `response_json_schema` | Python `dict` | From Pydantic `.model_json_schema()` |

### Known Issue: "too many states for serving"

Complex schemas may be rejected. Simplification checklist:
- Property names 1-3 chars (e.g., `n` not `recipe_name`)
- No `enum` values — guide choices in prompt instead
- No `minimum`/`maximum` constraints
- Nesting 3 levels deep maximum
- Prefer arrays of primitives over arrays of objects

### Resolving Pydantic `$ref` References

Gemini doesn't handle `$defs`/`$ref`. Resolve before passing:

```python
def resolve_schema_refs(schema: dict) -> dict:
    if "$defs" not in schema:
        return schema
    defs = schema.pop("$defs")
    def _resolve(s):
        if "$ref" in s:
            ref = s.pop("$ref")
            s.update(defs[ref.split("/")[-1]])
        if "properties" in s:
            for prop in s["properties"].values():
                _resolve(prop)
        if "items" in s:
            _resolve(s["items"])
    _resolve(schema)
    return schema
```

## Common Patterns

### JSON Generation
```python
from app.ai.gemini_client import generate_text
result = await generate_text(prompt="Generate JSON...", temperature=0.8)
data = json.loads(result)
```

### Generation with Token Tracking
```python
text, metadata = await generate_text_with_metadata(prompt="...")
# metadata: {model_name, prompt_tokens, completion_tokens, total_tokens}
```

### Vision / Photo Analysis
```python
result = await analyze_image(image_base64=b64, media_type="image/jpeg")
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "too many states" | Simplify schema (short names, flatten, remove constraints) |
| 404 model not found | Check model name constant |
| Empty response | Implement retry with exponential backoff |
| Timeout | Use `asyncio.wait_for()` wrapper |
| `MissingGreenlet` | Using sync client — must use `client.aio` |
| `ServiceUnavailableError` | API key not configured |

## References

- google-genai SDK: https://github.com/googleapis/python-genai
- Structured output: https://ai.google.dev/gemini-api/docs/structured-output
