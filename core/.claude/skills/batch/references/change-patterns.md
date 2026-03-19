# Common Change Patterns

Real-world examples for the most frequent codebase-wide changes.

## Rename Symbol Across Codebase

**Scenario:** Rename a function, class, variable, or file everywhere it appears.

```
Change: Rename class `UserService` → `AccountService`

Search patterns:
  - Class name: "UserService"
  - File name: "UserService" or "user-service" or "user_service"
  - Variable instances: "userService", "user_service"
  - Type annotations: ": UserService", "<UserService>"
  - Import paths: from '.*UserService' or from '.*user-service'
  - Mock/stub names: "MockUserService", "UserServiceStub"
  - Test descriptions: "UserService should..."

Batch grouping:
  1. Pre-work: Rename file, rename class definition, update barrel export
  2. Parallel: Update each consuming module independently
  3. Post-work: Update config paths, regenerate imports

Gotchas:
  - Database table names or column names that match — do NOT rename (schema migration needed separately)
  - Environment variables like USER_SERVICE_URL — coordinate with ops team
  - API response bodies that include the class name as a string — breaking change for clients
  - Third-party code or vendored dependencies — do not modify
```

## Migrate API v1 to v2

**Scenario:** An internal or external API changed its interface. Update all callers.

```
Change: Migrate from `httpClient.get(url, callback)` → `httpClient.get(url): Promise`

Search patterns:
  - "httpClient.get(" with callback argument
  - "httpClient.post(" with callback argument
  - ".get(url, function" and ".get(url, (err"

Transformation:
  BEFORE:
    httpClient.get('/api/users', (err, response) => {
      if (err) { handleError(err); return; }
      processUsers(response.data);
    });

  AFTER:
    try {
      const response = await httpClient.get('/api/users');
      processUsers(response.data);
    } catch (err) {
      handleError(err);
    }

Batch grouping:
  1. Pre-work: Update httpClient wrapper to support both old and new API (shim)
  2. Parallel: Migrate each module's callers independently
  3. Post-work: Remove the compatibility shim, run full suite

Gotchas:
  - Functions calling httpClient must become async (cascading signature change)
  - Error handling patterns differ (callback err vs try/catch)
  - Test mocks need updating (mock callback invocation → mock Promise resolution)
  - Some callers may use the callback for streaming — different migration path
```

## Update Dependency Usage

**Scenario:** A dependency released a new major version with API changes.

```
Change: Migrate from `moment.js` → `date-fns`

Search patterns:
  - "import moment" or "require('moment')"
  - "moment(" — constructor calls
  - ".format(" — moment-specific method
  - ".add(", ".subtract(" — moment duration methods
  - ".isValid(", ".isBefore(", ".isAfter(" — moment comparison methods

Transformation map:
  moment()                    → new Date()
  moment(dateStr)             → parseISO(dateStr)
  moment().format('YYYY-MM') → format(new Date(), 'yyyy-MM')
  moment().add(1, 'days')    → addDays(new Date(), 1)
  moment().isBefore(other)   → isBefore(date, other)

Batch grouping:
  1. Pre-work: Install date-fns, create adapter module with both APIs
  2. Parallel: Migrate each module (services, utils, components)
  3. Post-work: Remove moment from package.json, remove adapter, run suite

Gotchas:
  - Timezone handling differs significantly between moment and date-fns
  - moment objects are mutable; date-fns returns new Date objects
  - Some moment plugins (moment-timezone) need separate migration
  - Format string syntax differs ('YYYY' → 'yyyy', 'DD' → 'dd')
```

## Apply Code Pattern (Callbacks to Async/Await)

**Scenario:** Modernize callback-based code to use async/await throughout.

```
Change: Convert callback-style functions to async/await

Search patterns:
  - "function.*callback\)" — functions accepting callbacks
  - "callback(null," — success callback invocations
  - "callback(err" — error callback invocations
  - ".then(" followed by ".catch(" — promise chains to simplify

Transformation:
  BEFORE:
    function getUser(id, callback) {
      db.query('SELECT * FROM users WHERE id = ?', [id], (err, rows) => {
        if (err) { callback(err); return; }
        callback(null, rows[0]);
      });
    }

  AFTER:
    async function getUser(id) {
      const rows = await db.query('SELECT * FROM users WHERE id = ?', [id]);
      return rows[0];
    }

Batch grouping:
  1. Pre-work: Ensure db.query returns a Promise (promisify if needed)
  2. Parallel: Convert each service file independently
  3. Post-work: Update all callers to use await instead of callbacks

Gotchas:
  - Callers of converted functions must also become async (cascading change)
  - Error handling shifts from callback(err) to try/catch
  - Some callbacks are event-style (not error-first) — different conversion pattern
  - Streams and event emitters should NOT be converted to async/await
```

## Update Import Paths After Directory Restructure

**Scenario:** Moved files to a new directory structure, need to update all imports.

```
Change: Moved src/utils/ → src/shared/utils/ and src/helpers/ → src/shared/helpers/

Search patterns:
  - "from '../utils/" or "from '../../utils/"
  - "from '../helpers/" or "from '../../helpers/"
  - "require('./utils/" or "require('../utils/"

Transformation:
  - All imports from 'utils/' → 'shared/utils/'
  - All imports from 'helpers/' → 'shared/helpers/'
  - Relative path depth may change depending on the importing file's location

Batch grouping:
  1. Pre-work: Move directories, update tsconfig/webpack path aliases
  2. Parallel: Update imports in each top-level module directory
  3. Post-work: Verify no broken imports, run full suite

Gotchas:
  - Relative path depth changes based on the importing file's directory level
  - Path aliases in tsconfig/webpack may mask the actual import paths
  - Jest moduleNameMapper may need updating
  - Dynamic imports (import()) with string paths need manual attention
```

## Replace Deprecated Function Calls

**Scenario:** A function is deprecated and callers must switch to the replacement.

```
Change: Replace `logger.warn()` → `logger.warning()` (aligning with Python logging levels)

Search patterns:
  - "logger.warn("
  - "log.warn("
  - ".warn(" preceded by a logger variable

Transformation:
  logger.warn("message")  → logger.warning("message")
  logger.warn("msg", ctx) → logger.warning("msg", ctx)

Batch grouping: Simple enough for a single pass — one agent per top-level directory.

Gotchas:
  - console.warn() should NOT be changed (different API)
  - Some logger.warn() calls may have different argument signatures
  - Ensure logger.warning() actually exists in the logger interface
```

## Add/Remove Function Parameter Across All Call Sites

**Scenario:** A function signature changed — a parameter was added or removed.

```
Change: Add `options: RequestOptions` parameter to `apiClient.request(method, url)` →
        `apiClient.request(method, url, options: RequestOptions = {})`

Search patterns:
  - "apiClient.request(" — all call sites
  - "request(method, url)" — function definition and overrides
  - Mock/stub definitions that match the old signature

Transformation:
  BEFORE: apiClient.request('GET', '/users')
  AFTER:  apiClient.request('GET', '/users', {})
  OR:     apiClient.request('GET', '/users', { timeout: 5000 })

Batch grouping:
  1. Pre-work: Update function definition with default parameter value
  2. Parallel: Update call sites that need non-default options
  3. Post-work: Update type definitions, mocks, and tests

Gotchas:
  - If the new parameter has a default value, existing call sites MAY not need changes
  - Spread operators: request(...args) — the args array length changed
  - Interface/type definitions must be updated alongside the implementation
  - Overloaded functions need all overload signatures updated
```
