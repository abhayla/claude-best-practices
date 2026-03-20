# Verification Workflow

### Verification Workflow

After running each Maestro group, perform visual comparison:

1. **Locate screenshots** — Find all `.png` files in `e2e/output/{group}/`
2. **Copy to current/** — Move screenshots to `e2e/maestro/current/{group}/` for organized comparison
3. **Compare against baselines** — For each screenshot in `current/{group}/`:
   - Check if a baseline exists in `e2e/maestro/baselines/{group}/`
   - If baseline exists → use Claude's multimodal `Read` tool to view both images
   - Compare current vs baseline visually for layout shifts, missing elements, color changes, or content differences
   - Determine pass/fail based on whether the screens look functionally identical
4. **Report results** — Each screenshot gets one of three verdicts:
   - `MATCH` — Current matches baseline, no visual regression
   - `VISUAL_REGRESSION` — Current differs from baseline in a meaningful way
   - `NEW` — No baseline exists yet (not a failure, but flagged for review)

```bash
