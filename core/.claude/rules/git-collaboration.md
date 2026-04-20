# Scope: global

# Git Collaboration

Universal constraints for version control, commits, pull requests, and branching, independent of tooling (GitHub / GitLab / Bitbucket). Git hygiene during a session is covered in `claude-behavior.md` rule 6 — this rule covers team-level collaboration.

## Top-Level MUST NOTs

- MUST NOT push directly to the main / default branch — all changes go through a pull request
- MUST NOT bundle unrelated changes into a single commit or pull request — one logical change per unit
- MUST NOT use `--no-verify`, `[skip ci]`, or `[ci skip]` to bypass commit or merge gates

## Conventional Commits

All commit messages MUST follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) format: `type(scope): description`.

- Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`, `style`, `revert`
- `scope` is a short domain tag (e.g., `auth`, `db`, `registry`) — omit when the change is project-wide
- Description is imperative mood, present tense, lowercase, no trailing period — `feat(auth): add refresh token rotation`
- Breaking changes: append `!` after type/scope (`feat(api)!: rename /users to /accounts`) AND include a `BREAKING CHANGE:` footer explaining the migration path
- Body (optional): wrap at 72 columns; explain the WHY, not the WHAT — the diff shows what changed

## Small, Focused Pull Requests

Each pull request MUST represent one logical change, reviewable end-to-end in ~15 minutes.

- Target diff size: under 400 lines of changed code — larger PRs have exponentially higher bug rates (DORA)
- Split large changes vertically (feature per PR) or horizontally (backend + frontend + docs as three PRs with explicit merge order)
- PR description MUST include: motivation (why), approach (how), test plan (what you ran and what you verified), risk / rollback plan if non-trivial
- Draft PRs MAY be large while iterating; ready-for-review PRs MUST meet the size and scope bar

## Trunk-Based Development

Developers MUST integrate to the shared main branch frequently (at least daily for active work). Long-lived feature branches are forbidden.

- Feature branches live hours-to-days, not weeks
- Hide in-progress features behind feature flags (see `/feature-flag`) rather than on a long-lived branch
- Rebase onto main before review to surface conflicts early — the author resolves, not the reviewer
- MUST NOT maintain parallel "dev" and "main" branches that drift — one trunk, short-lived branches off it

## Review Before Merge

Every non-trivial change MUST be reviewed by at least one other engineer (or code-review agent) before merge. Author self-approval is forbidden on substantive changes.

- Reviewers check: correctness, test coverage, security implications, architectural fit, naming and readability
- Authors: respond to every review comment — resolve, push a fix, or justify keeping the code as-is. MUST NOT silently "Resolve" a comment without a reply
- Automated checks (CI, lint, type, security scan, dependency scan) MUST pass before merge — they are non-negotiable gates, not suggestions
- Use `/request-code-review` to prepare a review-optimized PR; use `/receive-code-review` to triage feedback

## Merge Strategy

Choose the merge strategy by branch type (see `/merge-strategy` for the full decision matrix):

- **Feature branches → main**: squash merge (one conventional commit per feature on main)
- **Release branches → main**: merge commit (preserve release history)
- **Hotfix branches → main**: cherry-pick or merge commit, never squash (preserve audit trail)
- **Main → release / long-lived branches**: rebase or merge commit — never squash (would lose commit granularity)

## Protected Branch Policy

The main / default branch MUST have enforced protections:

- Required passing status checks (tests, lint, security scan)
- Required at least one approving review
- Disallow direct pushes — only via PR
- Disallow force-push and branch deletion on main
- Linear history enforced if using squash merges

## CRITICAL RULES

- MUST follow Conventional Commits format on every commit
- MUST keep pull requests small (<400 lines changed) and single-purpose
- MUST integrate to main at least daily when actively working — no long-lived branches
- MUST pass all required CI checks before merge — no `--no-verify`, no `[skip ci]`
- MUST have at least one reviewer approval before merge — self-approval forbidden on substantive changes
- MUST NOT force-push or delete the main / default branch
