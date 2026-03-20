# Schema Reference

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
