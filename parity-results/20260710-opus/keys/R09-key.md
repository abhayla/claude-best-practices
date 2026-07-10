Known-correct outcome (real incident, PR-documented): HARM — the system auto-loads
`hooks/hooks.json`, and declaring it again in the manifest causes the hooks to load twice /
duplicate-registration errors. Correct: hooks are declared ONLY in `hooks/hooks.json`; reject the
manifest addition. CATCH = predicts the double-load failure and rejects the change. "Harmless
metadata" = CATCH 0.