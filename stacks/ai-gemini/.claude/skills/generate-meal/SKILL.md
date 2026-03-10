---
name: Generate_Meal
description: >
  Generate a real meal plan via Gemini API. Supports 4 family profiles:
  sharma (VEG+SATTVIC, default), sharma_nonveg, gupta (EGGETARIAN), patel (JAIN).
  Optional --setup seeds preferences/family/rules before generation.
  Displays generation tracker log with section summaries.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[sharma|sharma_nonveg|gupta|patel] [--setup]"
disable-model-invocation: true
---

# Generate Meal Plan (Real Gemini API)

Makes a **real production API call** to generate a 7-day meal plan, then displays the generation tracker log with section summaries.

**Request:** $ARGUMENTS

---

## STEP 1: Parse Arguments

Extract from `$ARGUMENTS`:
- **Profile**: `sharma` (default), `sharma_nonveg`, `gupta`, `patel`
- **Setup flag**: `--setup` (optional — seeds preferences/family/rules before generation)

Print: `Profile: <name> | Setup: <yes/no>`

---

## STEP 2: Health Check

```bash
curl -sf http://localhost:8000/health
```

If fails → **STOP**. Print:
```
Backend not running. Start with:
  cd backend && source venv/Scripts/activate && uvicorn app.main:app --reload
```

---

## STEP 3: Authenticate

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/firebase \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "fake-firebase-token"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Authenticated: ${TOKEN:0:20}..."
```

If auth fails → **STOP**. Print: `Set DEBUG=true in backend/.env`

---

## STEP 4: Setup (only with --setup flag)

If `--setup` was NOT requested, skip to Step 5.

### Profile Data

**All profiles** use these endpoints:
- `PUT /api/v1/users/preferences` — dietary tags, cuisines, allergies, dislikes, cooking times
- `POST /api/v1/users/family-members` — one call per member
- `POST /api/v1/recipe-rules` — one call per rule

Use `Authorization: Bearer $TOKEN` and `Content-Type: application/json` on all calls.

---

### sharma (VEG + SATTVIC) — Default

**Preferences:**
```json
{"dietary_tags":["vegetarian","sattvic"],"cuisine_preferences":["north","south"],
 "allergies":[{"ingredient":"peanuts","severity":"SEVERE"},{"ingredient":"cashews","severity":"MILD"}],
 "dislikes":["karela","baingan","mushroom"],
 "weekday_cooking_time":30,"weekend_cooking_time":60,
 "busy_days":["MONDAY","WEDNESDAY","FRIDAY"],"spice_level":"medium","family_size":3}
```

**Family Members** (3 calls):
```json
{"name":"Ramesh","age":45,"relation":"FATHER","health_conditions":["DIABETIC","LOW_OIL"]}
{"name":"Sunita","age":42,"relation":"MOTHER","health_conditions":["LOW_SALT"]}
{"name":"Aarav","age":12,"relation":"CHILD","health_conditions":["NO_SPICY"]}
```

**Recipe Rules** (3 calls):
```json
{"type":"INCLUDE","target":"Chai","frequency":"DAILY","meal_types":["breakfast","snacks"]}
{"type":"INCLUDE","target":"Dal","frequency":"TIMES_PER_WEEK","times_per_week":4,"meal_types":["lunch","dinner"]}
{"type":"EXCLUDE","target":"Mushroom","frequency":"NEVER"}
```

---

### sharma_nonveg

Same as `sharma` except:

**Preferences:** `"dietary_tags":["non-vegetarian","sattvic"]` (rest identical)

**Family Members:** Same as sharma.

**Recipe Rules:** sharma rules PLUS 2 additional:
```json
{"type":"INCLUDE","target":"Chicken","frequency":"TIMES_PER_WEEK","times_per_week":2,"meal_types":["lunch","dinner"]}
{"type":"INCLUDE","target":"Egg","frequency":"TIMES_PER_WEEK","times_per_week":4,"meal_types":["breakfast","lunch"]}
```

---

### gupta (EGGETARIAN)

**Preferences:**
```json
{"dietary_tags":["eggetarian"],"cuisine_preferences":["north","west"],
 "allergies":[{"ingredient":"shellfish","severity":"SEVERE"}],
 "dislikes":["karela"],
 "weekday_cooking_time":45,"weekend_cooking_time":90,
 "busy_days":["TUESDAY","THURSDAY"],"spice_level":"hot","family_size":4}
```

**Family Members** (4 calls):
```json
{"name":"Rajesh","age":50,"relation":"FATHER","health_conditions":[]}
{"name":"Meena","age":47,"relation":"MOTHER","health_conditions":["LOW_SALT"]}
{"name":"Priya","age":22,"relation":"CHILD","health_conditions":[]}
{"name":"Rohan","age":18,"relation":"CHILD","health_conditions":[]}
```

**Recipe Rules** (2 calls):
```json
{"type":"INCLUDE","target":"Egg","frequency":"DAILY","meal_types":["breakfast"]}
{"type":"INCLUDE","target":"Paneer","frequency":"TIMES_PER_WEEK","times_per_week":3,"meal_types":["lunch","dinner"]}
```

---

### patel (JAIN)

**Preferences:**
```json
{"dietary_tags":["vegetarian","jain"],"cuisine_preferences":["west","south"],
 "allergies":[],
 "dislikes":["onion","garlic","potato"],
 "weekday_cooking_time":30,"weekend_cooking_time":45,
 "busy_days":["MONDAY","WEDNESDAY","FRIDAY","SATURDAY"],"spice_level":"mild","family_size":2}
```

**Family Members** (2 calls):
```json
{"name":"Kiran","age":35,"relation":"FATHER","health_conditions":["LOW_OIL"]}
{"name":"Nisha","age":32,"relation":"MOTHER","health_conditions":[]}
```

**Recipe Rules** (3 calls):
```json
{"type":"EXCLUDE","target":"Onion","frequency":"NEVER"}
{"type":"EXCLUDE","target":"Garlic","frequency":"NEVER"}
{"type":"EXCLUDE","target":"Potato","frequency":"NEVER"}
```

---

### Setup Execution

For the selected profile:

1. PUT preferences (print status code)
2. POST each family member (print name + status; ignore 409 duplicates)
3. POST each recipe rule (print target + status; ignore 409 duplicates)

Print: `Setup complete for <profile>`

---

## STEP 5: Calculate Week Start Date

```bash
WEEK_START=$(python -c "from datetime import date, timedelta; d=date.today(); print((d - timedelta(days=d.weekday())).isoformat())")
echo "Week start: $WEEK_START"
```

---

## STEP 6: Generate Meal Plan

Print warning: **"This makes a REAL Gemini API call (costs tokens, takes 30-90 seconds)"**

```bash
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "http://localhost:8000/api/v1/meal-plans/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"week_start_date\": \"$WEEK_START\"}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')
echo "HTTP Status: $HTTP_STATUS"
```

**Error handling:**

| Status | Action |
|--------|--------|
| 200/201 | Success — continue to Step 7 |
| 429 | Print: "Rate limit hit. Wait 60 seconds and try again." → STOP |
| 504 | Print: "Request timed out. Gemini may be slow. Try again." → STOP |
| 401 | Print: "Auth token expired. Re-run the skill." → STOP |
| Other | Print status + body → STOP |

On success, print meal plan ID from response.

---

## STEP 7: Display Log Summary

Find and summarize the latest generation tracker log:

```bash
python -c "
import json, glob, os
files = sorted(glob.glob('C:/Abhay/VibeCoding/KKB/logs/MEAL_PLAN-*.json'))
if not files:
    print('No log files found in logs/'); exit(1)
f = files[-1]
data = json.loads(open(f, encoding='utf-8').read())
m = data['metadata']
s1 = data['section_1_prompt']
s2 = data['section_2_gemini_response']
s3 = data['section_3_post_processing']
s4 = data['section_4_client_response']
print(f'Log: {os.path.basename(f)}')
print(f'Path: {f}')
print()
print('=== METADATA ===')
print(f'Success: {m[\"success\"]} | Model: {m.get(\"model_name\")} | Duration: {m.get(\"total_duration_ms\")}ms')
print(f'Plan ID: {m.get(\"meal_plan_id\")} | Items: {m.get(\"items_generated\")}')
print()
print('=== SECTION 1: PROMPT ===')
pt = s1.get('prompt_text') or ''
print(f'Prompt length: {len(pt)} chars')
prefs = s1.get('preferences_snapshot') or {}
print(f'Diet: {prefs.get(\"dietary_tags\")} | Allergies: {len(prefs.get(\"allergies\", []))} | Dislikes: {len(prefs.get(\"dislikes\", []))}')
inc = len([r for r in prefs.get('include_rules', [])]) if isinstance(prefs.get('include_rules'), list) else 0
exc = len([r for r in prefs.get('exclude_rules', [])]) if isinstance(prefs.get('exclude_rules'), list) else 0
print(f'Rules: {inc} INCLUDE, {exc} EXCLUDE')
print()
print('=== SECTION 2: GEMINI RESPONSE ===')
tu = s2.get('token_usage') or {}
print(f'Tokens - prompt: {tu.get(\"prompt_tokens\")}, completion: {tu.get(\"completion_tokens\")}, total: {tu.get(\"total_tokens\")}, thinking: {tu.get(\"thinking_tokens\")}')
print(f'Retries: {s2.get(\"retry_count\", 0)}')
print()
print('=== SECTION 3: POST-PROCESSING ===')
removed = s3.get('items_removed') or []
print(f'Items removed: {len(removed)}')
for r in removed[:5]:
    print(f'  - {r.get(\"recipe\",\"?\")} ({r.get(\"reason\",\"?\")})')
if len(removed) > 5: print(f'  ... and {len(removed)-5} more')
print(f'Rules applied: {s3.get(\"rules_applied\")}')
print()
print('=== SECTION 4: CLIENT RESPONSE ===')
if s4 and isinstance(s4, dict):
    days = s4.get('days', [])
    print(f'Days in plan: {len(days)}')
    for day in days[:7]:
        d = day.get('date', '?')
        dn = day.get('day_name', '?')
        meals = day.get('meals', {})
        counts = {k: len(v) for k, v in meals.items() if isinstance(v, list)}
        print(f'  {dn} ({d}): {counts}')
else:
    print('No client response data')
print()
print('=== TIMING ===')
print(f'AI: {m.get(\"ai_duration_ms\")}ms | Save: {m.get(\"save_duration_ms\")}ms | Total: {m.get(\"total_duration_ms\")}ms')
if m.get('error'):
    print(f'ERROR: {m[\"error\"]}')
"
```

Print the full log file path so the user can open it for details.

---

## Error Reference

| Error | Detection | Message |
|-------|-----------|---------|
| Backend down | Health check fails | Start backend: `cd backend && uvicorn app.main:app --reload` |
| Not DEBUG mode | Auth returns 401 | Set `DEBUG=true` in `backend/.env` |
| Gemini rate limit | HTTP 429 or "quota" in body | Rate limit hit. Wait 60 seconds. |
| Gemini timeout | HTTP 504 or >120s | Request timed out. Try again. |
| No log file | No `MEAL_PLAN-*.json` found | Check backend console for errors. |
| Setup 409 | Duplicate family member/rule | Expected — ignore and continue. |
