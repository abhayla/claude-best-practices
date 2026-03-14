---
name: supply-chain-audit
description: >
  Supply chain security audit: dependency inventory, vulnerability scanning,
  typosquatting detection, abandoned package identification, license compliance,
  dependency health scoring, and lockfile integrity verification. Based on
  Trail of Bits supply chain risk auditing patterns. Use for dependency audits,
  CVE checks, or pre-merge dependency review.
allowed-tools: "Bash Read Grep Glob"
triggers: "supply chain, dependency audit, npm audit, pip audit, typosquatting, vulnerable dependency, CVE"
argument-hint: "<'full-audit' or 'scan <package-name>' or 'license-check' or 'lockfile-verify'>"
version: "1.0.0"
type: workflow
---

# Supply Chain Audit

Audit the software supply chain for vulnerable, malicious, abandoned, or non-compliant dependencies.

**Request:** $ARGUMENTS

---

## STEP 1: Dependency Inventory

Enumerate all direct and transitive dependencies.

### Detect Package Ecosystem

```bash
# Identify manifest files
find . -maxdepth 3 \( \
  -name "package.json" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "pnpm-lock.yaml" \
  -o -name "requirements.txt" -o -name "Pipfile" -o -name "Pipfile.lock" -o -name "pyproject.toml" -o -name "poetry.lock" \
  -o -name "Cargo.toml" -o -name "Cargo.lock" \
  -o -name "go.mod" -o -name "go.sum" \
  -o -name "Gemfile" -o -name "Gemfile.lock" \
  -o -name "pom.xml" -o -name "build.gradle" -o -name "build.gradle.kts" \
  \) 2>/dev/null
```

### Extract Dependencies

| Ecosystem | List Direct | List All (Transitive) |
|-----------|-------------|----------------------|
| npm | `npm ls --depth=0` | `npm ls --all` |
| pip | `pip freeze` or parse `requirements.txt` | `pipdeptree` |
| Cargo | `cargo metadata --no-deps` | `cargo tree` |
| Go | `go list -m -json all` | `go mod graph` |
| Ruby | `bundle list` | `bundle viz` (graphviz) |
| Maven | `mvn dependency:list` | `mvn dependency:tree` |
| Gradle | `gradle dependencies --configuration runtimeClasspath` | Same with `--scan` |

### Dependency Count Summary

Record totals in this format:

```
Ecosystem: [npm/pip/cargo/go/...]
Direct dependencies: X
Transitive dependencies: Y
Total unique packages: Z
```

---

## STEP 2: Vulnerability Scanning

Run ecosystem-specific vulnerability scanners.

### Scanner Commands

```bash
# Node.js / npm
npm audit --json > npm-audit.json 2>/dev/null
npm audit --audit-level=high

# Python / pip
pip-audit --format=json --output=pip-audit.json 2>/dev/null
pip-audit

# Python / safety (alternative)
safety check --json --output=safety-report.json 2>/dev/null

# Rust / Cargo
cargo audit --json > cargo-audit.json 2>/dev/null
cargo audit

# Ruby / Bundler
bundle-audit check --update
bundle-audit check --format=json > bundle-audit.json 2>/dev/null

# Go
govulncheck ./... 2>&1 | tee govulncheck-report.txt

# Multi-ecosystem (if available)
osv-scanner --format=json --output=osv-report.json -r . 2>/dev/null
```

### Triage Vulnerability Results

For each CVE/advisory found:

| Field | Description |
|-------|-------------|
| **CVE/GHSA ID** | Unique identifier |
| **Package** | Affected package name and version |
| **Severity** | CVSS score and qualitative rating |
| **Fixed in** | Version that resolves the issue |
| **Reachability** | Is the vulnerable code path actually called? |
| **Exploitability** | Is there a public exploit or PoC? |
| **Upgrade path** | Can the fix be applied without breaking changes? |

---

## STEP 3: Typosquatting Detection

Check for packages that may be impersonations of popular libraries.

### Common Typosquatting Patterns

| Pattern | Example | Legitimate |
|---------|---------|-----------|
| Character swap | `reqeusts` | `requests` |
| Prefix addition | `python-requests` | `requests` |
| Suffix addition | `requests-py` | `requests` |
| Hyphen/underscore swap | `python_dateutil` vs `python-dateutil` | Check PyPI/npm directly |
| Scope squatting (npm) | `@my-org/lodash` | `lodash` |
| Combosquatting | `requests-utils` | `requests` + `utils` |

### Detection Workflow

```bash
# Extract all package names from manifests
# npm
cat package.json | python3 -c "
import json, sys
pkg = json.load(sys.stdin)
for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
    for name in pkg.get(dep_type, {}):
        print(name)
" 2>/dev/null | sort

# pip (requirements.txt)
grep -v "^#\|^$\|^-" requirements.txt 2>/dev/null | sed 's/[><=!].*//' | sed 's/\[.*//' | sort

# For each package, verify:
# 1. Package exists on the official registry
# 2. Package name is not suspiciously similar to a popular package
# 3. Publisher/maintainer is consistent with expectations
```

### Red Flags

- Package published within last 30 days with a name similar to a popular package
- Single maintainer with no other packages
- Package description copied from another package
- Minimal or empty source code with install hooks (`preinstall`, `postinstall`)
- Sudden spike in downloads followed by plateau

---

## STEP 4: Abandoned Package Detection

Identify unmaintained dependencies that may accumulate unpatched vulnerabilities.

### Health Indicators

| Indicator | Healthy | Warning | Abandoned |
|-----------|---------|---------|-----------|
| Last publish | < 6 months | 6-18 months | > 18 months |
| Open issues ratio | < 30% | 30-60% | > 60% |
| Maintainer count | 2+ | 1 | 0 or unresponsive |
| Last commit | < 3 months | 3-12 months | > 12 months |
| CI status | Passing | Flaky | Failing or absent |
| Deprecation notice | None | Soft deprecation | Officially deprecated |

### Check Commands

```bash
# npm: check package metadata
npm view <package-name> time --json 2>/dev/null | python3 -c "
import json, sys
from datetime import datetime, timezone
data = json.load(sys.stdin)
latest = max(v for k, v in data.items() if k not in ('created', 'modified'))
age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(latest.replace('Z', '+00:00'))).days
print(f'Last published: {latest} ({age_days} days ago)')
"

# npm: check maintainers
npm view <package-name> maintainers --json 2>/dev/null

# PyPI: check release history
pip index versions <package-name> 2>/dev/null
```

---

## STEP 5: License Compliance

Identify license obligations and incompatibilities.

### SPDX License Identification

```bash
# npm: list all licenses
npx license-checker --json --production > licenses.json 2>/dev/null
npx license-checker --summary --production

# pip: list licenses
pip-licenses --format=json --output-file=licenses.json 2>/dev/null
pip-licenses --summary

# Cargo
cargo license --json > licenses.json 2>/dev/null

# Go
go-licenses report ./... 2>/dev/null
```

### License Compatibility Matrix

| License | Permissive Use | Must Distribute Source | Copyleft Risk |
|---------|---------------|----------------------|---------------|
| MIT | Yes | No | None |
| Apache-2.0 | Yes | No (patent grant) | None |
| BSD-2/3 | Yes | No | None |
| ISC | Yes | No | None |
| MPL-2.0 | Yes | File-level only | Low |
| LGPL-2.1/3.0 | Yes (dynamic link) | Modified LGPL files | Medium |
| GPL-2.0/3.0 | Restricted | Entire combined work | High |
| AGPL-3.0 | Restricted (network use) | Entire combined work | Critical |
| SSPL | Restricted | Entire stack | Critical |
| Unlicensed / NONE | Unknown | Unknown | Requires legal review |

### Red Flags

- Any AGPL/SSPL dependency in a proprietary SaaS product
- GPL dependency linked statically into a non-GPL project
- Dependencies with no license file or `UNLICENSED` marker
- License changed between versions (check changelog)

---

## STEP 6: Lockfile Integrity Verification

Verify lockfiles are present, consistent, and untampered.

### Verification Checks

```bash
# npm: verify lockfile integrity
npm ci --dry-run 2>&1 | head -20

# Check for lockfile existence
for lockfile in package-lock.json yarn.lock pnpm-lock.yaml Pipfile.lock poetry.lock Cargo.lock Gemfile.lock go.sum; do
  if [ -f "$lockfile" ]; then
    echo "FOUND: $lockfile ($(wc -l < "$lockfile") lines)"
  fi
done

# Check lockfile is in version control
git ls-files --error-unmatch package-lock.json 2>/dev/null && echo "Tracked" || echo "NOT tracked in git"

# Detect lockfile/manifest drift
npm ls 2>&1 | grep "WARN\|ERR" | head -10
```

### Lockfile Checklist

- [ ] Lockfile exists for every manifest file
- [ ] Lockfile is tracked in git (not `.gitignore`d)
- [ ] Lockfile matches manifest (no drift: run `npm ci` or `pip install --require-hashes`)
- [ ] Integrity hashes present (npm: `integrity` field; pip: `--require-hashes`)
- [ ] No unexpected registry URLs (check for private registry tampering)
- [ ] Lockfile was not manually edited (check git blame for human edits)

---

## STEP 7: Remediation

Prioritize and fix identified issues.

### Remediation Priority

| Priority | Criteria | Action |
|----------|----------|--------|
| P0 — Immediate | Known exploited CVE, critical severity | Upgrade or patch within 24 hours |
| P1 — Urgent | High severity CVE with public PoC | Upgrade within 1 week |
| P2 — Standard | Medium severity or no public exploit | Upgrade in next release cycle |
| P3 — Track | Low severity, no exploit, defense-in-depth | Add to backlog, monitor |

### Upgrade Strategies

```bash
# npm: check for available upgrades
npm outdated --long
npx npm-check-updates

# pip: check for upgrades
pip list --outdated --format=json

# Direct upgrade (single package)
npm install <package>@latest
pip install --upgrade <package>

# Major version upgrade (test thoroughly)
npx npm-check-updates -u --target=latest
npm install
npm test
```

### When Direct Upgrade Breaks Compatibility

1. **Pin to latest safe version** that fixes the CVE without breaking changes
2. **Find alternative package** with equivalent functionality and better maintenance
3. **Vendor the dependency** and apply the security patch manually (last resort)
4. **Accept the risk** with documented justification and compensating controls (e.g., WAF rule)

---

## Output Format: Supply Chain Report

```markdown
## Supply Chain Audit Report

**Repository:** [name]
**Date:** [audit date]
**Ecosystems:** [npm, pip, cargo, ...]

### Summary
| Category | Count |
|----------|-------|
| Direct dependencies | X |
| Transitive dependencies | Y |
| Known vulnerabilities | Z |
| Typosquatting suspects | N |
| Abandoned packages | N |
| License issues | N |
| Lockfile issues | N |

### Vulnerabilities (by severity)
#### Critical
- **CVE-XXXX-XXXXX** in `package@version` — [description]. Fix: upgrade to `version`.

### Typosquatting Suspects
- `package-name` — similar to `legitimate-package`. [Verified safe / Needs investigation]

### Abandoned Dependencies
- `package@version` — last published X months ago, Y open issues

### License Concerns
- `package@version` — GPL-3.0 (copyleft risk in proprietary project)

### Recommendations
1. [Priority-ordered action items]
```

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `npm audit` returns no results | Private registry without advisory database | Use `osv-scanner` as an alternative cross-ecosystem scanner |
| `pip-audit` not found | Not installed | Install via `pip install pip-audit` |
| Lockfile drift detected | Manual edits or partial installs | Delete lockfile, run clean install (`npm ci` / `pip install`), recommit |
| License checker shows "UNKNOWN" | Package missing license field in metadata | Check the package repository directly for LICENSE file |
| Scanner reports CVE in dev dependency | Dev-only dependency not in production | Document as lower risk but still upgrade — dev dependencies run in CI |
| Too many transitive vulnerabilities | Deep dependency tree with old nested deps | Use `npm audit fix --force` cautiously or override specific versions with `overrides` field |
| Typosquatting check flags legitimate package | Name is genuinely similar to another | Verify on official registry; document as reviewed and safe |

---

## CRITICAL RULES

### MUST DO

- Scan ALL ecosystems present in the project — do not skip secondary manifests (e.g., docs site `package.json`)
- Verify lockfile existence and git tracking for every manifest
- Check reachability for each CVE — transitive vulnerabilities in unused code paths are lower priority
- Include CVSS score and exploitability assessment for every vulnerability reported
- Provide specific upgrade commands for each remediation recommendation
- Flag any dependency with no license as requiring legal review
- Record the scanner versions used in the report for reproducibility

### MUST NOT DO

- Mark a CVE as "not applicable" without verifying the code path is unreachable — use call graph analysis instead
- Recommend `npm audit fix --force` without reviewing what major version bumps it introduces
- Ignore dev/build dependencies — they execute in CI/CD pipelines which are privileged environments
- Trust package names at face value — always verify against the official registry
- Skip lockfile verification — lockfile tampering is a documented supply chain attack vector
- Report license issues without checking the actual license file — metadata can be outdated or wrong
