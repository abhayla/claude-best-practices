---
description: Bun runtime and ElysiaJS framework patterns and conventions
globs: ["**/src/**/*.ts", "**/server/**/*.ts"]
---

# Bun + ElysiaJS Development Rules

## Bun Runtime

### Use Bun-native APIs when available
- File I/O: `Bun.file()`, `Bun.write()` instead of `fs`
- Hashing: `Bun.hash()`, `Bun.password.hash()` instead of `crypto`
- SQLite: `bun:sqlite` instead of `better-sqlite3`
- Testing: `bun:test` instead of Jest (compatible API)
- Environment: `Bun.env` instead of `process.env` (both work, `Bun.env` is typed)

### Package management
- Use `bun install` (not `npm install`) — uses `bun.lockb` binary lockfile
- Use `bun add` / `bun remove` for dependency management
- Run scripts with `bun run` or directly: `bun src/index.ts`
- Use `bunx` instead of `npx` for one-off executables

### Running and building
```bash
bun run src/index.ts          # run TypeScript directly (no build step)
bun --watch src/index.ts      # watch mode
bun build src/index.ts --outdir dist --target bun   # bundle for production
```

## ElysiaJS Patterns

### Route definitions — chain methods for type inference
```typescript
// CORRECT: chained for end-to-end type safety
const app = new Elysia()
  .get("/users", () => getUsers())
  .post("/users", ({ body }) => createUser(body))
  .listen(3000);

// WRONG: separate statements lose type inference
const app = new Elysia();
app.get("/users", () => getUsers());  // types not propagated
```

### Validation with built-in schema (TypeBox)
```typescript
import { Elysia, t } from "elysia";

new Elysia()
  .post("/users", ({ body }) => createUser(body), {
    body: t.Object({
      email: t.String({ format: "email" }),
      name: t.String({ minLength: 1 }),
    }),
  });
```

### Plugins — use `.use()` for composition
```typescript
const authPlugin = new Elysia({ name: "auth" })
  .derive(({ headers }) => {
    const token = headers.authorization?.replace("Bearer ", "");
    return { userId: token ? verifyToken(token) : null };
  });

const app = new Elysia()
  .use(authPlugin)
  .get("/me", ({ userId }) => getUser(userId));  // userId available via derive
```

### WebSockets — use built-in Bun WebSocket support
ElysiaJS `.ws()` uses Bun's native WebSocket (pub/sub built-in). Prefer `ws.subscribe()`/`ws.publish()` over manual connection tracking.

### Error handling
```typescript
new Elysia()
  .onError(({ code, error }) => {
    if (code === "NOT_FOUND") return { error: "Not found" };
    if (code === "VALIDATION") return { error: error.message };
    return { error: "Internal server error" };
  });
```

## Anti-Patterns

- NEVER use `node:` prefixed imports unless the package explicitly requires Node.js — Bun implements most Node APIs without the prefix
- NEVER use `bun.lockb` and `package-lock.json` in the same project — pick one package manager
- NEVER use `setTimeout`/`setInterval` for high-precision timing — use `Bun.sleep()` or `Bun.nanoseconds()`
- NEVER ignore Elysia's type inference by using separate route registration — always chain `.get().post()` on the same instance
