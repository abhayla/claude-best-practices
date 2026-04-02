# Post-Promotion Lifecycle

What happens to a skill AFTER it ships: security vetting, deployment
governance, monitoring, versioning, and deprecation.

## 8.1 Security Review Gate

**Read:** `security-review.md` for the full vetting process — risk tier
assessment (7 indicators), 8-step review checklist, and grep commands.

**When security review is required:**

| Trigger | Review Level |
|---|---|
| New skill (any source) | Full review — all 8 steps |
| Major version update | Full review — behavioral changes may alter risk profile |
| Minor/patch version update | Diff review — compare against previously reviewed version |
| Periodic re-review | Quarterly for deployed skills — context drift can introduce risk |
| Third-party/external skill | Full review — treat as untrusted code |

**Separation of duties:** The skill author MUST NOT be the sole reviewer.
A second person (or automated tooling) must complete the security review
checklist independently. This prevents blind spots and catches adversarial
patterns the author may overlook.

## 8.2 Deployment Governance

### Registry requirements

When adding to `registry/patterns.json`, include:

| Field | Purpose |
|---|---|
| name, type, category | Identification and classification |
| version | SemVer — tracks what's deployed |
| hash | Integrity verification at deployment time |
| dependencies | What the skill requires (other skills, agents, MCP servers) |
| owner | Team or individual responsible for maintenance |
| eval_status | Last evaluation date and result (PASS/FIX/FAIL) |

### Integrity verification

- **Compute checksums** of reviewed skills and verify them at deployment
- **Use signed commits** in the skill repository to ensure provenance
- **Pin to specific versions** in production — never deploy `latest`
  without running the full evaluation suite first

## 8.3 Monitor and Detect Drift

Skills degrade silently as workflows change and models evolve. Watch for
these signals:

| Signal | What It Means | Action |
|---|---|---|
| Users rephrase and re-invoke | Triggers too narrow | Add natural language triggers |
| Skill activates for unrelated requests | Triggers too broad | Narrow description, add boundaries |
| Users skip steps manually | Steps unnecessary or wrong order | Restructure workflow |
| Users always modify the output | Output format doesn't match needs | Update templates |
| Errors in later steps | Earlier steps missed validation | Add prerequisite checks |
| Declining eval scores on periodic re-run | Model or workflow drift | Re-evaluate, update instructions |

**Periodic re-evaluation:** Re-run the skill's evaluation suite quarterly
(or after model updates) to detect regressions. Compare against the
baseline from the last promotion. If scores decline, trigger Step 8.4.

**Usage observation:** When possible, review how Claude uses the skill
in real workflows. See `iterative-development.md` for the Claude A/B
observation methodology and `eval-driven-iteration.md` for the
navigation observation checklist.

## 8.4 Version Management

### Before promoting a new version

1. Run the **full evaluation suite** — no partial passes
2. Complete **security review** per 8.1 (full for MAJOR, diff for MINOR/PATCH)
3. Compare against **baseline** using `/skill-evaluator full <path> --baseline`
4. Update registry entry (version, hash, eval_status)

### Rollback plan

- **Maintain the previous version** as a fallback (Git history or tagged release)
- If a new version fails evaluations in production, revert to the last
  known-good version immediately
- The deprecation workflow (Step 8.5) preserves old versions for 2 cycles,
  providing a natural rollback window

### Version bump rules

| Change Type | Version Bump | Security Review | Eval Required |
|---|---|---|---|
| Wording fix, typo | PATCH (0.0.x) | Diff review | Targeted re-test |
| New optional content, reference file | MINOR (0.x.0) | Diff review | Full suite |
| Breaking output/arg changes, step restructure | MAJOR (x.0.0) | Full review | Full suite + baseline comparison |

## 8.5 Deprecation Lifecycle

When a skill needs to be retired or replaced:

1. **Add deprecation fields** to the old skill's frontmatter:
   ```yaml
   deprecated: true
   deprecated_by: replacement-skill-name
   ```

2. **Keep the deprecated skill** for 2 version cycles — downstream
   projects may still reference it

3. **Update the replacement skill's description** to mention it replaces
   the old one (aids discovery during transition)

4. **After 2 cycles**, remove the deprecated skill and update the registry

**When to deprecate:**
- Evaluations consistently fail and fixes don't improve scores
- The workflow the skill supports has been retired
- A better skill fully supersedes this one (confirmed by evals)
- Persistent coexistence conflicts that can't be resolved by narrowing

MUST NOT delete a skill without the deprecation lifecycle. Abrupt removal
breaks downstream projects.

## 8.6 Scaling Considerations

### Recall limits

Every skill's metadata (name + description) is loaded at startup and
competes for attention. With too many skills active, Claude may fail
to select the right one or miss relevant ones entirely.

- **Monitor recall accuracy** as you add skills — use evaluations to
  measure whether existing skills still trigger correctly
- **Stop adding** when trigger accuracy degrades for existing skills
- **Consolidate narrow skills** into broader ones when patterns emerge
  (e.g., merge `formatting-sales-reports` + `querying-pipeline-data`
  into `sales-operations` — only when evals confirm equivalent performance)

### Role and stack-based bundling

Limit what each user loads to keep the active skill set focused:
- **By stack:** Android developers load `android-*` skills, not `fastapi-*`
  (this is how `recommend.py --provision` works)
- **By role:** Sales team loads CRM/pipeline skills, engineering loads
  code review/deployment skills
- Each bundle should contain only skills relevant to daily workflows

### When to consolidate

| Signal | Action |
|---|---|
| Two skills share 50%+ of steps | Consolidate into one with modes |
| Trigger conflicts between related skills | Merge or clearly differentiate |
| User confusion about which skill to invoke | Simplify the set |
| Eval confirms consolidated skill matches individual performance | Safe to merge |
