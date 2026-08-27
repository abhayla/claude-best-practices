# Fast-lane runbook (T-349/T-351/T-353)

The eligibility list and the lane rule live in `SKILL.md` STEP 3; this file is the command
sequence a dispatching session runs once a contract is declared `lane: fast`.

**FLOW:** contract with `lane: fast`, `files:`, `checks:` (<=2 min) -> `python
GWD/fast-lane-gate.py contract <path>` (its 20-26 code table is in the script header; any block
routes to the normal lane) -> `stage-stamp.py <T> edit_start` -> the DISPATCHING SESSION edits in a
FRESH worktree of the TARGET repo (`git worktree add <repo-path>-wt-<tid> -b <branch>
origin/main`; never the cwd checkout, never the bus) after reading `context_docs` -> commit, push,
open the PR -> `stage-stamp.py <T> edit_end` -> `fast-lane-gate.py diff <worktree> --base
origin/main` (a block => `lane: normal` + status_log note, dispatch normally) -> CHECKER `python
GWD/fast-lane-check.py <contract> <worktree> --base origin/main --evidence
GWD/evidence/<date>-<T>/` -> merge on green -> `stage-stamp.py <T> merged` -> LEDGER line from
`stage-stamp.py ledger-line <T>`. SLO <=20 min launched->merged
(`settings.fast_lane_slo_minutes`); a miss surfaces as `FAST-LANE-SLO-MISS` via `lesson.py
status`. A `lane: fast` contract reaching WORKER dispatch is preflight exit 14.

Every gate here is deterministic: `fast-lane-gate.py` (contract + diff modes, exit table 20-26 in
its header) and `fast-lane-check.py` (the checker, writes the evidence dir). A block from either
routes the task back to the normal lane - it is never overridden by judgment.
