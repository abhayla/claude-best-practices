---
name: firebase-data-connect
description: >
  Firebase Data Connect (PostgreSQL + GraphQL), Hosting (static sites/SPAs),
  and App Hosting (Next.js/Angular SSR). Use when working with Data Connect schemas,
  queries, mutations, security, vector search, or deploying web apps to Firebase.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<what to build — e.g. 'create movie review schema' or 'deploy Next.js app'>"
---

# Firebase Data Connect & Hosting

Reference for Data Connect (PostgreSQL-backed GraphQL), static Hosting, and App Hosting.

**Request:** $ARGUMENTS

---

## Data Connect Overview

Firebase Data Connect is a PostgreSQL-backed GraphQL service. It auto-generates an implicit `id: UUID!` primary key for each `@table` type.

### Project Structure

```
dataconnect/
  dataconnect.yaml          # Service config
  schema/
    schema.gql              # Type definitions
  connector/
    connector.yaml           # SDK generation config
    queries.gql              # Query operations
    mutations.gql            # Mutation operations
```

### Emulator

```bash
npx -y firebase-tools@latest emulators:start --only dataconnect
```

```typescript
import { getDataConnect, connectDataConnectEmulator } from 'firebase/data-connect';
const dc = getDataConnect(app, connectorConfig);
if (import.meta.env.DEV) {
  connectDataConnectEmulator(dc, 'localhost', 9399);
}
```

---

## Schema Reference

### Defining Types

```graphql
type Movie @table {
  # id: UUID! is auto-added
  title: String!
  releaseYear: Int
  genre: String
}
```

### Customizing Tables

```graphql
type Movie @table(name: "movies", key: "id", singular: "movie", plural: "movies") {
  id: UUID! @col(name: "movie_id") @default(expr: "uuidV4()")
  title: String!
  releaseYear: Int @col(name: "release_year")
  genre: String @col(dataType: "varchar(20)")
}
```

### User Table with Auth

```graphql
type User @table(key: "uid") {
  uid: String! @default(expr: "auth.uid")
  email: String! @unique
  displayName: String @col(dataType: "varchar(100)")
  createdAt: Timestamp! @default(expr: "request.time")
}
```

### Core Directives

| Directive | Purpose | Key Arguments |
|-----------|---------|---------------|
| `@table` | Define a database table | `name`, `key`, `singular`, `plural` |
| `@col` | Customize column mapping | `name`, `dataType`, `size` (for Vector) |
| `@default` | Set default value | `value` (literal), `expr` (CEL), `sql` (raw SQL) |
| `@unique` | Unique constraint | On field or `@unique(fields: [...])` on type |
| `@index` | Database index | `fields`, `order` (`ASC`/`DESC`), `type` (`BTREE`/`GIN`/`HNSW`) |
| `@searchable` | Enable full-text search | `language` (default: `"english"`) |

### Default Expressions

| Expression | Description |
|------------|-------------|
| `uuidV4()` | Generate UUID |
| `auth.uid` | Current user's Firebase Auth UID |
| `request.time` | Server timestamp |

### Relationships

```graphql
# One-to-many: Movie has many Reviews
type Review @table {
  movie: Movie!    # Creates foreign key
  user: User!
  rating: Int!
}
# Access: movie.reviews_on_movie, review.movie

# Many-to-many via join table
type MovieActor @table(key: ["movie", "actor"]) {
  movie: Movie!
  actor: Actor!
  role: String!
}
# Access: movie.actors_via_MovieActor, actor.movies_via_MovieActor
```

### Data Types

`String`, `Int`, `Int64`, `Float`, `Boolean`, `Date`, `Timestamp`, `UUID`, `Any`, `Vector`

---

## Operations Reference

### Auto-Generated Fields

For each `@table` type, Data Connect generates:

| Field | Purpose |
|-------|---------|
| `movie(id: UUID!)` | Get single record |
| `movies(where: ..., orderBy: ..., limit: ..., offset: ...)` | List/filter records |
| `movie_insert(data: ...)` | Create record |
| `movie_insertMany(data: [...])` | Bulk create |
| `movie_update(id: ..., data: ...)` | Update by ID |
| `movie_updateMany(where: ..., data: ...)` | Bulk update |
| `movie_upsert(data: ...)` | Insert or update |
| `movie_delete(id: ...)` | Delete by ID |
| `movie_deleteMany(where: ...)` | Bulk delete |

### Queries

```graphql
# Basic query
query GetMovie($id: UUID!) @auth(level: PUBLIC) {
  movie(id: $id) {
    id title genre releaseYear
  }
}

# List with filtering, sorting, pagination
query ListMovies($genre: String, $minRating: Int) @auth(level: PUBLIC) {
  movies(
    where: {
      genre: { eq: $genre },
      rating: { ge: $minRating }
    },
    orderBy: [{ releaseYear: DESC }, { title: ASC }],
    limit: 20,
    offset: 0
  ) {
    id title genre rating
  }
}
```

### Filter Operators

| Operator | Description |
|----------|-------------|
| `eq`, `ne` | Equals / not equals |
| `gt`, `ge`, `lt`, `le` | Comparison |
| `in`, `nin` | In / not in list |
| `isNull` | Null check |
| `contains`, `startsWith`, `endsWith` | String matching |
| `includes` | Array includes |

### Expression Operators (Server-Side Comparison)

```graphql
# Compare with auth values using _expr suffix
query MyPosts @auth(level: USER) {
  posts(where: { authorUid: { eq_expr: "auth.uid" }}) {
    id title
  }
}
```

### Mutations

```graphql
# Create
mutation CreateMovie($title: String!, $genre: String) @auth(level: USER) {
  movie_insert(data: { title: $title, genre: $genre })
}

# Update
mutation UpdateMovie($id: UUID!, $title: String!) @auth(level: USER) {
  movie_update(id: $id, data: { title: $title })
}

# Upsert
mutation UpsertUser @auth(level: USER) {
  user_upsert(data: {
    uid_expr: "auth.uid",
    email_expr: "auth.token.email"
  })
}

# Delete
mutation DeleteMovie($id: UUID!) @auth(level: USER) {
  movie_delete(id: $id)
}
```

### Multi-Step Transactions

```graphql
mutation TransferCredits($from: UUID!, $to: UUID!, $amount: Int!)
  @auth(level: USER) @transaction {
  from: account_update(id: $from, data: { credits_dec: $amount })
  to: account_update(id: $to, data: { credits_inc: $amount })
}
```

---

## Security Reference

### @auth Directive

Every deployable query/mutation MUST have `@auth`. Without it, operations default to `NO_ACCESS`.

| Level | Who Can Access |
|-------|----------------|
| `PUBLIC` | Anyone (authenticated or not) |
| `USER_ANON` | Any authenticated user (including anonymous) |
| `USER` | Authenticated users (excludes anonymous) |
| `USER_EMAIL_VERIFIED` | Users with verified email |
| `NO_ACCESS` | Admin SDK only |

### CEL Expressions

```graphql
# Custom claims
@auth(expr: "auth.token.role == 'admin'")

# Verified email domain
@auth(expr: "auth.token.email_verified && auth.token.email.endsWith('@company.com')")

# Multiple conditions
@auth(expr: "auth.uid != nil && (auth.token.role == 'editor' || auth.token.role == 'admin')")
```

### Available Bindings

| Binding | Description |
|---------|-------------|
| `auth.uid` | Current user's Firebase UID |
| `auth.token.email` | User's email |
| `auth.token.email_verified` | Email verified boolean |
| `auth.token.firebase.sign_in_provider` | `password`, `google.com`, etc. |
| `auth.token.<custom_claim>` | Custom claims via Admin SDK |
| `vars` | Operation variables |
| `request.time` | Server timestamp |

### @check and @redact

```graphql
# Validate data exists before allowing operation
mutation UpdateMovie($id: UUID!, $title: String!)
  @auth(level: USER) @transaction {
  # Check user has editor role
  userRole: user(key: { uid_expr: "auth.uid" }) @redact {
    role @check(expr: "this == 'editor'", message: "Must be editor")
  }
  movie_update(id: $id, data: { title: $title })
}
```

### Security Anti-Patterns

| Anti-Pattern | Use Instead |
|-------------|-------------|
| Missing `@auth` directive | Always add `@auth` to every operation |
| `@auth(level: PUBLIC)` on mutations | Use `USER` or higher with data filtering |
| Trusting client-provided UIDs | Use `eq_expr: "auth.uid"` for ownership checks |
| No `@check` for role-based access | Validate roles via `@check` + `@redact` |

---

## Vector Similarity Search

Semantic search using Vertex AI embeddings and PostgreSQL `pgvector`.

### Schema

```graphql
type Movie @table {
  title: String!
  description: String
  descriptionEmbedding: Vector! @col(size: 768)
}
```

### Generate Embeddings

```graphql
mutation CreateMovieWithEmbedding($title: String!, $description: String!)
  @auth(level: USER) {
  movie_insert(data: {
    title: $title,
    description: $description,
    descriptionEmbedding_embed: {
      model: "textembedding-gecko@003",
      text: $description
    }
  })
}
```

### Similarity Query

```graphql
query SearchMovies($query: String!) @auth(level: PUBLIC) {
  movies_descriptionEmbedding_similarity(
    compare_embed: { model: "textembedding-gecko@003", text: $query },
    method: COSINE,
    within: 2.0,
    limit: 5
  ) {
    id title description
    _metadata { distance }
  }
}
```

| Parameter | Description |
|-----------|-------------|
| `compare_embed` | Generate embedding from text via Vertex AI |
| `compare` | Raw Vector for pre-computed embeddings |
| `method` | `L2`, `COSINE`, or `INNER_PRODUCT` |
| `within` | Max distance threshold |

---

## Full-Text Search

```graphql
# Schema: enable with @searchable
type Movie @table {
  title: String! @searchable
  description: String @searchable(language: "english")
}

# Query: auto-generated _search fields
query SearchMovies($query: String!) @auth(level: PUBLIC) {
  movies_search(
    query: $query,
    queryFormat: QUERY,
    relevanceThreshold: 0.05,
    limit: 20
  ) {
    id title description
    _metadata { relevance }
  }
}
```

| Query Format | Description |
|-------------|-------------|
| `QUERY` | Web-style (default): quotes, AND, OR |
| `PLAIN` | Match all words, any order |
| `PHRASE` | Exact phrase match |
| `ADVANCED` | Full tsquery syntax |

---

## SDK Generation

### Configuration (connector.yaml)

```yaml
connectorId: my-connector
generate:
  javascriptSdk:
    outputDir: "../web-app/src/lib/dataconnect"
    package: "@movie-app/dataconnect"
  kotlinSdk:
    outputDir: "../android-app/app/src/main/kotlin/com/example/dataconnect"
    package: "com.example.dataconnect"
  swiftSdk:
    outputDir: "../ios-app/DataConnect"
```

Generate: `npx -y firebase-tools@latest dataconnect:sdk:generate`

### Web SDK Usage

```typescript
import { listMovies, createMovie, getMovie } from '@movie-app/dataconnect';
import { listMoviesRef, subscribe } from '@movie-app/dataconnect';

// Query
const result = await listMovies();
console.log(result.data.movies);

// Mutation
const newMovie = await createMovie({ title: 'New Movie', genre: 'Action' });

// Realtime subscription
const unsubscribe = subscribe(listMoviesRef(), {
  onNext: (result) => console.log(result.data),
  onError: (error) => console.error(error),
});
```

---

## Firebase Hosting (Static Sites)

For static sites and SPAs without SSR.

### Configuration (firebase.json)

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "cleanUrls": true,
    "rewrites": [
      { "source": "**", "destination": "/index.html" }
    ],
    "redirects": [
      { "source": "/old-page", "destination": "/new-page", "type": 301 }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [{ "key": "Cache-Control", "value": "max-age=31536000" }]
      }
    ]
  }
}
```

### Deploy

```bash
# Standard deploy
npx -y firebase-tools@latest deploy --only hosting

# Preview channel (temporary URL for testing)
npx -y firebase-tools@latest hosting:channel:deploy preview-name

# Clone preview to live
npx -y firebase-tools@latest hosting:clone SOURCE:preview-name TARGET:live
```

---

## Firebase App Hosting (SSR Frameworks)

For Next.js, Angular, and other frameworks with SSR/ISR. Requires Blaze plan.

### When to Use Which

| Use Case | Service |
|----------|---------|
| Static HTML/CSS/JS, SPA (React/Vue without SSR) | Firebase Hosting |
| Next.js / Angular with SSR or ISR | App Hosting |
| Automated git-push-to-deploy | App Hosting |

### Configuration (apphosting.yaml)

```yaml
runConfig:
  minInstances: 0
  maxInstances: 4
  cpu: 1
  memoryMiB: 512
  concurrency: 80

env:
  - variable: NEXT_PUBLIC_API_URL
    value: "https://api.example.com"
  - variable: API_KEY
    secret: my-api-key    # References Cloud Secret Manager
```

### firebase.json

```json
{
  "apphosting": {
    "backendId": "my-app-id",
    "rootDir": "/",
    "ignore": ["node_modules", ".git", "functions"]
  }
}
```

### CLI Commands

```bash
# List backends
npx -y firebase-tools@latest apphosting:backends:list

# Manage secrets
npx -y firebase-tools@latest apphosting:secrets:set SECRET_NAME
npx -y firebase-tools@latest apphosting:secrets:grantaccess SECRET_NAME

# Deploy
npx -y firebase-tools@latest deploy

# Manual rollout (for GitHub CI/CD setups)
npx -y firebase-tools@latest apphosting:rollouts:create BACKEND_ID --git-branch main
```

### Local Emulation (apphosting.emulator.yaml)

```yaml
emulators:
  apphosting:
    port: 5174
```

---

## Security Best Practices

1. **Every operation needs `@auth`** -- Omitting it defaults to `NO_ACCESS`
2. **Use `eq_expr: "auth.uid"` for ownership** -- Never trust client-provided UIDs
3. **Validate with `@check` + `@redact`** -- Look up permissions in the database before mutations
4. **Start with `USER` level** -- Only use `PUBLIC` for truly public read-only data
5. **Use secrets for API keys** -- `apphosting:secrets:set` for App Hosting, never hardcode

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Schema deploy fails | Check GraphQL syntax, directive arguments, and type compatibility |
| SDK generation errors | Verify `connector.yaml` paths and run `dataconnect:sdk:generate` |
| Vector search no results | Check embedding model name, vector size matches `@col(size:)` |
| App Hosting deploy fails | Verify Blaze plan, check `apphosting.yaml` syntax |
| Preview channel expired | Channels auto-expire; redeploy with `hosting:channel:deploy` |

## References

- Data Connect: https://firebase.google.com/docs/data-connect
- Firebase Hosting: https://firebase.google.com/docs/hosting
- App Hosting: https://firebase.google.com/docs/app-hosting
- Data Connect Security: https://firebase.google.com/docs/data-connect/security
