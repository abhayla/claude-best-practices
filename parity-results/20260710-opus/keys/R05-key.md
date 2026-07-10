Known-correct outcome (real, recurring trap): the cache is version-pinned — an updater that sees
the SAME version `0.3.1` has nothing to fetch; a source edit without a **version bump** never
propagates. Missing step: bump the manifest version (e.g. 0.3.2), then the updater pulls the new
copy. CATCH = names the unbumped version as the root cause and the bump as the fix. DERIVE = traces
the cache-key logic. Answers like "users must reinstall" without identifying the version pin = at
most partial (judge's discretion, CATCH only if version-pinning is named).