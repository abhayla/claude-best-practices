---
name: monorepo
description: >
  Monorepo management patterns for npm/pnpm/yarn workspaces, Turborepo, and shared packages.
  Use when setting up, managing, or troubleshooting monorepo configurations.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[setup|workspace|shared|turborepo]"
version: "1.0.0"
type: reference
triggers: monorepo, workspaces, workspace, turborepo
---

# Monorepo Management Reference

Monorepo patterns for npm/pnpm/yarn workspaces with optional Turborepo orchestration.

## Workspace Setup

### npm Workspaces

```json
// package.json (root)
{
  "name": "my-monorepo",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev": "npm run dev --workspaces --if-present",
    "build": "npm run build --workspaces --if-present",
    "test": "npm run test --workspaces --if-present",
    "lint": "npm run lint --workspaces --if-present"
  }
}
```

### pnpm Workspaces

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

### Yarn Workspaces

```json
// package.json (root)
{
  "private": true,
  "workspaces": ["apps/*", "packages/*"]
}
```

## Directory Structure

```
monorepo/
├── package.json              # Root config + workspace definition
├── pnpm-workspace.yaml       # (pnpm only)
├── turbo.json                # (if using Turborepo)
├── apps/
│   ├── web/                  # Next.js / frontend app
│   │   ├── package.json
│   │   └── ...
│   ├── api/                  # Backend server
│   │   ├── package.json
│   │   └── ...
│   └── scraper/              # Worker / scraper
│       ├── package.json
│       └── ...
├── packages/
│   ├── shared/               # Shared types, utils, constants
│   │   ├── package.json
│   │   ├── src/
│   │   └── tsconfig.json
│   ├── ui/                   # Shared UI components
│   │   └── package.json
│   └── config/               # Shared configs (ESLint, TS, Tailwind)
│       └── package.json
└── tsconfig.json             # Root TypeScript config
```

## Shared Packages

### Creating a Shared Package

```json
// packages/shared/package.json
{
  "name": "@myorg/shared",
  "version": "0.0.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./types": "./src/types/index.ts",
    "./utils": "./src/utils/index.ts"
  },
  "scripts": {
    "typecheck": "tsc --noEmit"
  }
}
```

```typescript
// packages/shared/src/index.ts
export * from "./types";
export * from "./utils";
export * from "./constants";
```

### Consuming Shared Packages

```json
// apps/web/package.json
{
  "dependencies": {
    "@myorg/shared": "workspace:*"
  }
}
```

```typescript
// apps/web/src/page.tsx
import { UserSchema, formatDate } from "@myorg/shared";
```

### Package Manager Install Syntax

| Manager | Add workspace dependency | Add root dependency |
|---------|------------------------|---------------------|
| npm | `npm install @myorg/shared -w apps/web` | `npm install eslint -w .` |
| pnpm | `pnpm add @myorg/shared --filter apps/web` | `pnpm add -w eslint` |
| yarn | `yarn workspace apps/web add @myorg/shared` | `yarn add -W eslint` |

## Workspace Commands

### Running Scripts in Specific Workspaces

```bash
# npm
npm run dev -w apps/web
npm run test -w apps/api
npm run build --workspaces          # all workspaces

# pnpm
pnpm --filter web dev
pnpm --filter api test
pnpm --filter "./apps/*" build      # glob filter
pnpm -r build                       # all workspaces (recursive)

# yarn
yarn workspace web dev
yarn workspaces foreach run build
```

### Installing Dependencies

```bash
# npm — add to specific workspace
npm install zod -w apps/web

# npm — add to root (dev dependency)
npm install -D typescript

# pnpm — add to specific workspace
pnpm add zod --filter web

# pnpm — add to root
pnpm add -Dw typescript
```

## Turborepo Integration

### turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**", "out/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["build"]
    },
    "lint": {},
    "typecheck": {
      "dependsOn": ["^build"]
    }
  }
}
```

### Turborepo Commands

```bash
# Run task across all workspaces (with caching)
npx turbo build
npx turbo test
npx turbo lint

# Run for specific workspace
npx turbo build --filter=web
npx turbo dev --filter=web --filter=api

# Run with dependencies
npx turbo build --filter=web...      # web + all its dependencies

# Dry run (show what would execute)
npx turbo build --dry-run
```

### Task Dependencies

| Pattern | Meaning |
|---------|---------|
| `"dependsOn": ["^build"]` | Run `build` in dependencies first (topological) |
| `"dependsOn": ["build"]` | Run own `build` first |
| `"dependsOn": []` | No dependencies, can run immediately |
| `"cache": false` | Never cache (use for `dev` servers) |
| `"persistent": true` | Long-running task (use for `dev` servers) |

## TypeScript Configuration

### Root tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "composite": true
  }
}
```

### App tsconfig.json

```json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src",
    "paths": {
      "@myorg/shared": ["../../packages/shared/src"],
      "@myorg/shared/*": ["../../packages/shared/src/*"]
    }
  },
  "include": ["src"],
  "references": [
    { "path": "../../packages/shared" }
  ]
}
```

## Common Patterns

### Shared Environment Variables

```typescript
// packages/shared/src/env.ts
import { z } from "zod";

const baseEnvSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  DATABASE_URL: z.string().url(),
});

export function validateEnv<T extends z.ZodObject<z.ZodRawShape>>(
  schema: T,
): z.infer<T> {
  const result = schema.safeParse(process.env);
  if (!result.success) {
    console.error("Environment validation failed:", result.error.format());
    process.exit(1);
  }
  return result.data;
}

export { baseEnvSchema };
```

### Shared Database Schema (Drizzle)

```typescript
// packages/shared/src/db/schema.ts
// Define schema once, import in both web and api apps
export * from "./schema/users";
export * from "./schema/posts";
export * from "./schema/relations";
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `Cannot find module '@myorg/shared'` | Workspace link not established | Run `npm install` / `pnpm install` from root |
| Types not resolving from shared package | Missing `paths` in tsconfig | Add `paths` mapping and `references` |
| `npm run build` builds in wrong order | Missing dependency declaration | Add `"dependsOn": ["^build"]` in turbo.json or declare workspace deps |
| Duplicate dependencies | Package installed in multiple workspaces | Hoist to root or use `pnpm` (strict by default) |
| Lock file conflicts | Multiple devs adding deps | Always run install from root |
| `ERR_MODULE_NOT_FOUND` for shared code | Package exports not configured | Add `"exports"` field to shared package.json |
| Turbo cache not working | Outputs not declared | Add build output paths to `"outputs"` in turbo.json |

## CRITICAL RULES

### MUST DO
- Always run `npm install` / `pnpm install` from the monorepo root — never from individual workspace dirs
- Always declare workspace dependencies in each app's `package.json` (e.g., `"@myorg/shared": "workspace:*"`)
- Always use `"private": true` on the root `package.json` and shared packages that aren't published
- Always configure TypeScript `references` and `paths` for cross-workspace imports
- Use `workspace:*` (pnpm) or `*` (npm/yarn) for internal dependency versions

### MUST NOT DO
- NEVER publish internal workspace packages to npm unless intended — mark them `"private": true`
- NEVER install dependencies from within a workspace directory — always install from root
- NEVER duplicate shared types/utilities across workspaces — extract to a shared package
- NEVER use relative path imports (`../../packages/shared`) across workspaces — use the package name (`@myorg/shared`)
