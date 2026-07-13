**Not correct — it'll silently corrupt the second row.** Don't flip it on yet.

The spec says "comma-separated," but the sample data contains a quoted field with an embedded comma: `"Smith, John & Sons",42`. A naive split-on-comma turns that one line into three fields (`"Smith`, ` John & Sons"`, `42`) instead of two, and the customer name comes out wrapped in a stray quote with the wrong seat count alignment for anything after it. Row 1 and row 3 (`Acme Corp,120`, `Delta LLC,15`) look fine precisely because they have no embedded comma — that's what makes this bug easy to miss in a quick eyeball check.

This is proper CSV (RFC 4180 quoting), not plain delimiter-separated text, even though the spec's prose undersells it. Two fixes, pick one:
1. Swap the raw `.split(',')` for a real CSV parser (`csv` module in Python, `csv-parse`/Papa Parse in JS, etc.) that honors quoting.
2. If you want to keep it dependency-free, at minimum handle quoted fields with a small state machine — don't hand-roll a comma split.

**Risk if shipped as-is:** any partner whose customer name contains a comma (business names with "Inc," "LLC," "& Sons," suffixes are common) will get a garbled name and a seat count that's off by a field — and because the file has no header/checksum, this fails silently, not loudly. Given today's actual sample already contains this exact case, I'd treat it as confirmed-will-break, not hypothetical. I haven't seen your parser's code, so I can't confirm the exact one-line fix — if you paste it I can point to the precise change.