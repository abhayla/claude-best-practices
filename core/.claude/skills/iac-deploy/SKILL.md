---
name: iac-deploy
description: >
  Deploy infrastructure with Terraform and Pulumi covering provider configuration,
  resource management, state backends, module composition, environment management,
  drift detection, security hardening, CI/CD integration, FinOps, serverless
  deployment, and static site deployment.
  Use when planning, writing, reviewing, or troubleshooting IaC configurations.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "iac, terraform, pulumi, infrastructure, infrastructure as code, tf plan, tf apply, cloud provisioning"
argument-hint: "<'plan' or 'write <resource>' or 'review' or 'migrate-state' or 'modularize' or 'drift-check'>"
version: "1.1.0"
type: workflow
---

# Infrastructure as Code — Terraform & Pulumi

Deploy and manage cloud infrastructure using declarative IaC tools.

**Request:** $ARGUMENTS

---

## STEP 1: Assess the Infrastructure Context

Before writing any IaC, understand what already exists.

### 1.1 Discover Existing Configuration

```bash
# Terraform files
find . -name "*.tf" -o -name "*.tfvars" -o -name "*.tfstate" | head -40

# Pulumi files
find . -name "Pulumi.yaml" -o -name "Pulumi.*.yaml" -o -name "__main__.py" -o -name "index.ts" | head -40

# Check for lock files
find . -name ".terraform.lock.hcl" -o -name "package-lock.json" -o -name "requirements.txt" | head -20
```

### 1.2 Identify the IaC Tool

| Signal | Tool |
|--------|------|
| `*.tf` files, `.terraform/` directory | Terraform (HCL) |
| `Pulumi.yaml`, language-specific source files | Pulumi |
| Both present | Hybrid — clarify scope with user |
| Neither present | Greenfield — recommend based on team skills |

### 1.3 Check Provider/Cloud Target

```bash
# Terraform — extract providers
grep -r 'provider "' *.tf 2>/dev/null || echo "No Terraform providers found"
grep -r 'required_providers' *.tf 2>/dev/null

# Pulumi — check dependencies
cat Pulumi.yaml 2>/dev/null
cat requirements.txt 2>/dev/null | grep pulumi
cat package.json 2>/dev/null | grep pulumi
```

---

## STEP 2: Terraform Fundamentals

Provider configuration, data sources, variables, outputs, and locals.

**Read:** `references/terraform-fundamentals.md` for provider config examples, data source patterns, and variable/output/locals conventions with key rules.

---

## STEP 3: Pulumi Fundamentals

Project structure, stack configuration, and resource creation patterns.

**Read:** `references/pulumi-fundamentals.md` for Pulumi.yaml structure, stack config commands, and Python resource creation examples.

---

## STEP 4: State Management

Remote backends, state locking, migration, and importing existing resources.

**Read:** `references/state-management.md` for S3/GCS/Azure backend configs, Pulumi backends, DynamoDB lock tables, migration commands, and import patterns.

**Key rules:**
- MUST use remote state with locking for any shared or production infrastructure.
- MUST enable encryption on the state backend (state contains secrets in plaintext).
- NEVER manually edit state files — use `terraform state mv`, `terraform state rm`, or `pulumi state delete`.
- Use separate state files per environment.

---

## STEP 5: Module Composition

**Read:** `references/module-composition.md` for module structure, input/output contracts, calling modules, and versioning patterns.

**Key rules:**
- MUST version-pin all external module sources.
- MUST define clear input/output contracts with descriptions and validations.
- NEVER put provider blocks inside modules — providers are passed from root.
- Modules MUST be stateless — no backend configuration inside modules.

---

## STEP 6: Environment Management

Terraform workspaces, per-environment tfvars, and Pulumi stacks.

**Read:** `references/environment-management.md` for workspace commands, tfvars examples, and Pulumi stack-aware configuration.

---

## STEP 7: Drift Detection

Plan/preview before apply, detecting manual changes, and reconciliation.

**Read:** `references/drift-detection.md` for plan/preview commands, drift detection exit codes, reconciliation strategies, and scheduled CI drift checks.

---

## STEP 8: Security

Credential management, least-privilege IAM, and policy as code.

**Read:** `references/security-hardening.md` for OIDC federation, IAM role examples, OPA/Conftest policies, and security rules.

**Key rules:**
- NEVER commit credentials, access keys, or secrets to IaC files or tfvars.
- MUST use OIDC federation for CI/CD — no long-lived access keys.
- MUST mark sensitive variables and outputs with `sensitive = true`.
- MUST run policy-as-code checks (OPA/Conftest/Sentinel) in CI before apply.

---

## STEP 9: CI/CD Integration

> **Reference:** See [references/ci-cd-integration.md](references/ci-cd-integration.md) for GitHub Actions workflow templates (plan on PR, apply on merge), approval gates, pipeline state locking, and CI/CD rules.

---

## STEP 10: Common Resource Patterns, Refactoring, and Anti-Patterns

> **Reference:** See [references/resource-patterns.md](references/resource-patterns.md) for VPC/networking, compute, database, storage, DNS/CDN patterns, refactoring strategies (moved blocks, imports, state operations), and anti-patterns to avoid.

## STEP 11: FinOps — Cost Estimation & Optimization

> **Reference:** See [references/finops.md](references/finops.md) for Infracost integration, CI/CD cost checks, resource right-sizing, cost tagging strategy, budget alerts, and optimization checklist.

## STEP 12: Serverless & Static Site Deployment

> **Reference:** See [references/serverless-static.md](references/serverless-static.md) for Lambda/Cloud Functions, static site deployment (Vercel/Netlify/Cloudflare Pages/Firebase), SSR deployment, preview deployments, and Terraform/Pulumi command cheat sheets.

---

## CRITICAL RULES

- ALWAYS plan/preview before apply — never apply blindly
- ALWAYS use remote state with locking and encryption for shared infrastructure
- NEVER hardcode credentials, regions, account IDs, or resource identifiers
- NEVER apply and refactor state in the same operation
- ALWAYS pin provider and module versions
- ALWAYS tag resources with environment, project, and managed-by
- ALWAYS use separate state per environment
- ALWAYS review destroy/replace actions in plan output before applying
- Mark all sensitive variables and outputs as `sensitive = true`
- Use OIDC federation in CI/CD — no long-lived access keys
- ALWAYS run `infracost diff` on PRs that change infrastructure — cost surprises are deployment blockers
- ALWAYS tag all resources with Environment, Project, Team, and CostCenter
- ALWAYS configure budget alerts before provisioning production infrastructure
- ALWAYS use preview deployments for static sites — every PR gets a reviewable URL
- MUST NOT provision production infrastructure without a monthly cost estimate
- MUST NOT use NAT Gateway in dev environments — use NAT Instance or VPC endpoints instead
