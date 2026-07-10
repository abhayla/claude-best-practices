Known-correct outcome (real incident): the command is WRONG for this state. `checkout -b NEW
origin/main` carries over only *uncommitted* changes; the refactor is COMMITTED on the current
branch, so the new branch starts from origin/main WITHOUT those 3 commits and the working tree's
tracked files revert to main's versions — the work seems to vanish (it's still on the old branch).
Correct: branch off HEAD (`git checkout -b refactor/shared-landing`), or rename, or keep the current
branch. CATCH = predicts the loss mechanism and gives a HEAD-based alternative. Verification bonus:
suggest `git diff --name-only origin/main...NEW` after, to confirm the branch carries the change set.
"Yes, that's fine" = CATCH 0.