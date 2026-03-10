---
name: gemini-api
description: >
  Reference for Gemini API usage in RasoiAI: client setup, structured output (response_schema),
  meal generation, photo analysis, prompt patterns. Use when working with any Gemini-powered feature.
allowed-tools: "Bash Read Grep Glob Write Edit"
---

# Gemini API Reference

Quick-reference for all Gemini-powered features in RasoiAI.

---

## SDK & Client Setup

| Detail | Value |
|--------|-------|
| SDK | `google-genai` (NOT the old `google-generativeai`) |
| Client file | `backend/app/ai/gemini_client.py` |
| Model constant | `MODEL_NAME = "gemini-2.5-flash"` — change ONLY in `gemini_client.py` |
| API key env var | `GOOGLE_AI_API_KEY` |
| Config access | `settings.google_ai_api_key` (in `app/config.py`) |
| Initialization | Lazy — `get_gemini_client()` creates on first call |
| Async | Uses `client.aio.models.generate_content()` — NEVER use sync methods |

```python
# Client is a module-level singleton, lazily initialized
from google import genai
_client = genai.Client(api_key=settings.google_ai_api_key)

# All generation calls MUST use client.aio (native async)
response = await client.aio.models.generate_content(
    model=MODEL_NAME, contents=prompt, config=config
)
```

**Why `client.aio`?** Sync Gemini calls block the uvicorn event loop, stalling all concurrent requests. The old `google-generativeai` SDK had this problem. The `google-genai` SDK's `client.aio` is truly async.

---

## Key Functions

All in `backend/app/ai/gemini_client.py`:

| Function | Purpose | Returns |
|----------|---------|---------|
| `generate_text(prompt, temperature, max_output_tokens, response_schema, response_json_schema)` | JSON text generation | `str` (JSON) |
| `generate_text_with_metadata(prompt, ..., response_schema, response_json_schema)` | Same + token counts | `tuple[str, dict]` |
| `analyze_food_image(image_base64, media_type, prompt)` | Vision analysis | `dict` with `message` and `recipe_suggestions` |

All three raise `ServiceUnavailableError` if the API key is not configured. `generate_text` and `generate_text_with_metadata` always set `response_mime_type="application/json"`.

Default generation config:

```python
config = types.GenerateContentConfig(
    temperature=0.8,           # Creative but consistent
    max_output_tokens=65536,   # Full week meal plan with details
    response_mime_type="application/json",
    response_schema=response_schema,       # genai.types.Schema object
    response_json_schema=response_json_schema,  # Plain dict (preferred)
)
```

---

## Structured Output (response_schema)

Two parameters available in `generate_content()` config:

| Parameter | Type | Notes |
|-----------|------|-------|
| `response_schema` | `genai.types.Schema` object | Native SDK schema |
| `response_json_schema` | Plain Python `dict` | From Pydantic `.model_json_schema()` — **used for meal plans** |

### Known Issue: "too many states for serving"

Gemini 2.5 Flash rejects complex schemas. **Solved** by using short property names (1-3 chars) and flat structure. See `MEAL_PLAN_SCHEMA` in `ai_meal_service.py` for the working example.

Current meal plan schema uses: `d`=date, `dn`=day_name, `b`=breakfast, `l`=lunch, `di`=dinner, `s`=snacks, `n`=recipe_name, `t`=prep_time, `tags`=dietary_tags, `c`=category, `cal`=calories. The prompt explains these abbreviations.

**Root cause:** Schema complexity from long property names, nested arrays of objects, enum values, optional fields.

**Workaround if you need schema enforcement:**

Schema simplification checklist:
- [ ] Property names 1-3 chars (e.g., `n` not `recipe_name`)
- [ ] No `enum` values — guide choices in the prompt instead
- [ ] No `minimum`/`maximum` constraints
- [ ] No `date-time` format strings
- [ ] No `Optional` fields — make everything required or omit
- [ ] Nesting 3 levels deep maximum
- [ ] Prefer arrays of primitives over arrays of objects

### Resolving Pydantic `$ref` References

Gemini does not handle `$defs`/`$ref` in JSON schemas. If using Pydantic models to generate schemas, resolve references first:

```python
def resolve_schema_refs(schema: dict) -> dict:
    """Resolve $ref references in a JSON schema for Gemini compatibility."""
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

---

## Meal Generation Flow

Entry point: `AIMealService.generate_meal_plan()` in `backend/app/services/ai_meal_service.py`.

```
Load prefs + festivals + config
        |
    Build prompt (prefs, rules, allergies, festivals, pairing config)
        |
    generate_text_with_metadata() — JSON mime type + response_json_schema
        |
    _validate_response_structure() — 7 days, 4 slots each
        |
    _parse_response() → GeneratedMealPlan dataclass
        |
    _enforce_rules() — post-process: remove allergens, EXCLUDE items
        |
    MealGenerationContext → logged to logs/MEAL_PLAN-*.json
```

Key data classes (in `ai_meal_service.py`):
- `MealItem` — single recipe with name, prep time, tags, category
- `DayMeals` — breakfast/lunch/dinner/snacks lists for one day
- `GeneratedMealPlan` — 7 days + rules_applied summary
- `UserPreferences` — local dataclass (shadows `app.models.user.UserPreferences`)

Retry: 3 attempts with exponential backoff (1s, 2s, 4s).

---

## Common Patterns

### JSON Generation (no schema)

```python
from app.ai.gemini_client import generate_text

result = await generate_text(
    prompt="Generate a JSON object with...",
    temperature=0.8,
)
data = json.loads(result)
```

### JSON Generation with Schema (use short property names!)

```python
from app.ai.gemini_client import generate_text

# Use response_json_schema with SHORT keys to avoid "too many states"
result = await generate_text(
    prompt="...",
    response_json_schema={"type": "OBJECT", "properties": {"n": {"type": "STRING"}}, "required": ["n"]},
)
data = json.loads(result)
```

### Generation with Token Tracking

```python
from app.ai.gemini_client import generate_text_with_metadata

text, metadata = await generate_text_with_metadata(prompt="...")
# metadata: {model_name, prompt_tokens, completion_tokens, total_tokens, thinking_tokens}
```

### Vision / Photo Analysis

```python
from app.ai.gemini_client import analyze_food_image

result = await analyze_food_image(
    image_base64=base64_string,
    media_type="image/jpeg",  # or "image/png"
    prompt="Identify this dish...",  # optional, has a default
)
# result: {"message": "...", "recipe_suggestions": ["Palak Paneer", ...]}
```

---

## Where Gemini Is Used

| Feature | File | Function |
|---------|------|----------|
| Meal plan generation | `app/services/ai_meal_service.py` | `AIMealService.generate_meal_plan()` |
| Food photo analysis | `app/api/v1/endpoints/chat.py` | Uses `analyze_food_image()` |
| Gemini client wrapper | `app/ai/gemini_client.py` | All three exported functions |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "too many states for serving" | Simplify schema: short property names, flatten, remove constraints. Or drop schema and use prompt + post-validation. |
| 404 model not found | Check `MODEL_NAME` in `gemini_client.py`. Current: `gemini-2.5-flash`. |
| Empty response | Retry logic in `ai_meal_service.py` handles this (3 attempts). |
| Timeout (>120s) | Server uses `asyncio.wait_for(120)`. Increase if needed. Typical generation: 45-90s. |
| `MissingGreenlet` | Using sync Gemini client instead of `client.aio`. Must use async. |
| Stale imports | Clear `__pycache__`: `find backend -name "*.pyc" -delete && find backend -name "__pycache__" -type d -exec rm -rf {} +` |
| `ServiceUnavailableError` | `GOOGLE_AI_API_KEY` not set in `backend/.env`. |
| Rate limit (429) | Daily limits: 5 meal generations, 10 photo analyses. Configured in `app/config.py`. |

---

## Testing

```bash
cd backend

# Unit tests (mocked Gemini)
PYTHONPATH=. pytest tests/services/test_ai_meal_service.py -v

# Real API test (costs tokens) — use /generate-meal skill instead
# /generate-meal sharma --setup
```

Test file: `backend/tests/services/test_ai_meal_service.py` (~22 tests covering prompt building, response parsing, validation, rule enforcement, integration).

---

## References

- google-genai SDK: https://github.com/googleapis/python-genai
- Structured output docs: https://ai.google.dev/gemini-api/docs/structured-output
- Nested schema fix: https://github.com/googleapis/python-genai/issues/60
- Meal generation algorithm: `docs/design/Meal-Generation-Algorithm.md`
- Meal generation config: `docs/design/Meal-Generation-Config-Architecture.md`
