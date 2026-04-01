# Threat Model: Todo API

## Assets
- User credentials (email, password hash)
- Todo data (per-user isolation)
- JWT tokens

## Threats
1. **SQL Injection** — Mitigated by parameterized queries
2. **JWT Token Theft** — Mitigated by short-lived tokens (24h)
3. **Brute Force Login** — Not mitigated in v1.0 (planned rate limiting)
4. **IDOR on Todos** — Mitigated by user_id filter on all queries

## Risk Assessment
- Overall risk: LOW for MVP scope
- Critical gap: No rate limiting on auth endpoints
