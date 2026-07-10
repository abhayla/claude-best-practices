Known-correct outcome (real incident): Consent Mode defaults `analytics_storage:'denied'` and
nothing ever grants it (the comment says no `consent update` call exists) — so GA4 drops
measurement; the "0 users" is the direct, deterministic result of the snippet, not a backfill delay.
Fix: fire `gtag('consent','update',{analytics_storage:'granted'})` on consent (or default-grant
where lawful). CATCH = identifies denied-and-never-granted consent as the root cause and rejects
the wait-a-week theory. DERIVE = walks the snippet logic. "Wait and see" = CATCH 0.