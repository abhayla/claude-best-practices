Planted error: the new version changes semantics — for `page=1` old returns items[0:per_page], new
returns items[per_page:2*per_page]. The new code assumes 0-indexed pages while callers pass
1-indexed (old code's `page - 1` proves the convention). Page 1 silently skips the first page of
results. CATCH = identifies the off-by-one/indexing-convention break with a concrete example.
DERIVE = traces both versions for a specific page value. "Ship it" = CATCH 0.