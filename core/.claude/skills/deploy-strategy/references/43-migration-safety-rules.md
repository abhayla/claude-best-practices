# 4.3 Migration Safety Rules

### 4.3 Migration Safety Rules

| Rule | Why |
|------|-----|
| Never rename a column in one step | Old code references old name → crash |
| Never change a column type in one step | Old code expects old type → error |
| Never add NOT NULL without a default | Old code inserts without the column → crash |
| Never drop a column that's still read | Old instances read the column → error |
| Always separate DDL and DML migrations | Large data migrations lock tables |
| Always test migrations on a production-size dataset | Migrations that take seconds on dev take hours on prod |

