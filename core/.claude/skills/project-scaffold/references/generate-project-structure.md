# STEP 2: Generate Project Structure

### 2.1 Stack Templates

**Python (FastAPI/Django):**
```
<project>/
├── src/
│   ├── domain/           # Entities, value objects, domain errors
│   ├── application/      # Use cases, ports (interfaces)
│   ├── infrastructure/   # DB repos, external APIs, adapters
│   └── presentation/     # API routes, serializers, middleware
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── migrations/
├── scripts/
├── pyproject.toml
├── requirements.txt      # or poetry.lock / uv.lock
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── .semgrepconfig.yml
├── LICENSE
└── README.md
```

**Node/TypeScript (Next.js, Express, NestJS):**
```
<project>/
├── src/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── presentation/     # or app/ for Next.js
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── package.json
├── package-lock.json      # or pnpm-lock.yaml / yarn.lock
├── tsconfig.json
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .editorconfig
├── .gitignore
├── .husky/
│   └── pre-commit
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── .semgrepconfig.yml
├── commitlint.config.js
├── LICENSE
└── README.md
```

**React (Next.js + TypeScript):**
```
<project>/
├── src/
│   ├── app/                 # App Router (Next.js 13+)
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── api/
│   │   │   └── health/
│   │   │       └── route.ts
│   │   └── (routes)/        # Route groups
│   ├── components/
│   │   ├── ui/              # Reusable UI primitives
│   │   └── features/        # Feature-specific components
│   ├── lib/                 # Shared utilities, API clients
│   ├── hooks/               # Custom React hooks
│   └── types/               # TypeScript type definitions
├── public/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                 # Playwright tests
├── next.config.ts
├── package.json
├── package-lock.json
├── tsconfig.json
├── tailwind.config.ts       # If using Tailwind
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .env.local.example
├── .editorconfig
├── .gitignore
├── .husky/
│   └── pre-commit
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── .semgrepconfig.yml
├── commitlint.config.js
├── playwright.config.ts     # E2E test config
├── LICENSE
└── README.md
```

**Android (Compose + Kotlin):**
```
<project>/
├── app/
│   └── src/
│       ├── main/
│       │   ├── java/<package>/
│       │   │   ├── domain/
│       │   │   ├── data/
│       │   │   ├── di/
│       │   │   └── ui/
│       │   ├── AndroidManifest.xml
│       │   └── res/
│       ├── test/          # Unit tests
│       └── androidTest/   # Instrumented tests
├── build-logic/           # Convention plugins
├── gradle/
│   ├── libs.versions.toml
│   └── wrapper/
├── build.gradle.kts
├── settings.gradle.kts
├── gradle.properties
├── .editorconfig
├── .gitignore
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── LICENSE
└── README.md
```

**Go:**
```
<project>/
├── cmd/<app>/main.go
├── internal/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── handler/
├── pkg/                   # Public libraries (if any)
├── tests/
├── go.mod
├── go.sum
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .editorconfig
├── .gitignore
├── .golangci.yml
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── LICENSE
└── README.md
```

**Rust:**
```
<project>/
├── src/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── main.rs
├── tests/
├── Cargo.toml
├── Cargo.lock
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .editorconfig
├── .gitignore
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── clippy.toml
├── LICENSE
└── README.md
```

### 2.2 Shared Files (All Stacks)

Generate these regardless of stack:

**.editorconfig:**
```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{py,rs}]
indent_size = 4

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

**.env.example** — Document every variable with comments:
```bash
