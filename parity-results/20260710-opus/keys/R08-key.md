Known-correct outcome (real incident — the access existed in the infra SSOT + `~/.ssh/`): do NOT
report blocked yet. A secrets file is not the infra inventory; the stated context says an infra
SSOT exists and prior deploys happened — so the correct move is to check `GLOBAL.md` (and standard
key locations) BEFORE claiming a gap. CATCH = refuses to write the "blocked" update, checks/asks
for the SSOT first, and cites the prior-deploy signal. Writing the blocked status = CATCH 0.