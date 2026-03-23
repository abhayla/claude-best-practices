---
name: solidity-audit
description: >
  Audit and develop Solidity smart contracts covering Foundry/Hardhat testing,
  reentrancy protection, access control, gas optimization, upgrade patterns (UUPS,
  Transparent), oracle security, ERC standards, and Aderyn/Slither static analysis.
  Use when building, reviewing, or auditing smart contracts.
triggers:
  - solidity
  - smart contract
  - web3
  - foundry
  - hardhat
  - solidity audit
  - reentrancy
  - ERC-20
  - ERC-721
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<action: audit|develop|test|deploy|upgrade|optimize> <contract or description>"
version: "1.0.0"
type: workflow
---

# Solidity Audit — Smart Contract Development & Security

Production-grade Solidity development with security-first practices and audit methodology.

**Input:** $ARGUMENTS

---

## STEP 0: Private Key Safety Gate

**Before ANY operation**, check for exposed secrets:

```bash
# Scan for private keys, mnemonics, and API keys in the project
grep -rn "PRIVATE_KEY\|MNEMONIC\|0x[0-9a-fA-F]\{64\}\|secret\|api.key" \
  --include="*.sol" --include="*.js" --include="*.ts" --include="*.json" \
  --include="*.env" --include="*.toml" . 2>/dev/null | \
  grep -v "node_modules\|\.git\|artifacts\|cache"
```

**If ANY private key or mnemonic is found in source code:**
1. STOP immediately
2. Alert the user: `CRITICAL: Private key found in <file>:<line>. Move to .env and add to .gitignore.`
3. Do NOT proceed until resolved

**Verify .gitignore includes:**
```
.env
.env.local
broadcast/
cache/
out/
```

---

## STEP 1: Detect Action

| Action | Trigger | Description |
|--------|---------|-------------|
| `audit` | "audit", "security review" | Full security audit of contracts |
| `develop` | "create", "build", "implement" | Write new smart contracts |
| `test` | "test", "coverage", "fuzz" | Write and run tests |
| `deploy` | "deploy", "script" | Deployment scripts and verification |
| `upgrade` | "upgrade", "proxy", "UUPS" | Upgradeable contract patterns |
| `optimize` | "gas", "optimize", "efficient" | Gas optimization |

---

## STEP 2: Project Setup

### 2.1 Detect Framework

```bash
# Foundry project
test -f foundry.toml && echo "Foundry project"

# Hardhat project
test -f hardhat.config.js -o -f hardhat.config.ts && echo "Hardhat project"

# Neither
echo "No framework detected"
```

### 2.2 New Foundry Project (recommended)

```bash
forge init my-project
cd my-project

# Install OpenZeppelin
forge install OpenZeppelin/openzeppelin-contracts --no-commit

# Install Chainlink (for oracles)
forge install smartcontractkit/chainlink --no-commit

# Update remappings
echo '@openzeppelin/=lib/openzeppelin-contracts/
@chainlink/=lib/chainlink/' > remappings.txt
```

### 2.3 Project Structure

```
project/
  src/              # Contract source files
  test/             # Test files (.t.sol for Foundry)
  script/           # Deployment scripts (.s.sol)
  lib/              # Dependencies (git submodules)
  foundry.toml      # Foundry config
  .env              # Secrets (NEVER commit)
  .gitignore
```

---

## STEP 3: Development Patterns

**Read:** `references/development-patterns.md`

Covers contract structure, naming conventions, CEI pattern, access control, and emergency pause patterns.

---

## STEP 4: Testing (Foundry)

**Read:** `references/testing-guide.md`

Covers unit tests, fuzz testing, invariant testing, running tests (Foundry + Hardhat), and coverage.

---

## STEP 5: Security Audit (Cyfrin Methodology)

**Read:** `references/security-audit-checklist.md`

Run through 8 audit categories: Access Control, Reentrancy, Input Validation, Arithmetic, Oracle & External Data, Token Handling, Front-Running/MEV, Denial of Service.

---

## STEP 6: Upgrade Patterns

**Read:** `references/upgrade-patterns.md`

Covers UUPS upgradeable contracts, proxy deployment scripts, and upgrade safety rules.

---

## STEP 7: Gas Optimization

**Read:** `references/gas-optimization.md`

Covers storage packing, custom errors, caching storage reads, unchecked arithmetic, calldata vs memory, and gas measurement.

---

## STEP 8: Deployment

**Read:** `references/deployment-guide.md`

Covers Foundry deploy scripts, deploy commands (local/testnet/mainnet), and HelperConfig pattern.

---

## STEP 9: ERC Standards Reference

**Read:** `references/erc-standards.md`

Covers ERC-20, ERC-721, and ERC-1155 with OpenZeppelin examples.

---

## STEP 10: Verify & Report

### For Development

```bash
# Compile
forge build

# Test
forge test -vvv

# Coverage
forge coverage

# Gas snapshot
forge snapshot
```

### For Audit

```
Security Audit Report:
  Contract: {{name}}
  Solidity: {{version}}
  Framework: {{Foundry | Hardhat}}
  Lines of Code: {{count}}

  Static Analysis:
    Aderyn: {{findings count by severity}}
    Slither: {{findings count by severity}}

  Test Coverage:
    Statements: {{%}}
    Branches: {{%}}
    Functions: {{%}}

  Checklist:
    Access Control: {{PASS | FAIL — details}}
    Reentrancy: {{PASS | FAIL — details}}
    Input Validation: {{PASS | FAIL — details}}
    Oracle Security: {{PASS | FAIL — details}}
    Token Handling: {{PASS | FAIL — details}}
    MEV Protection: {{PASS | FAIL — details}}
    DoS Resistance: {{PASS | FAIL — details}}
    Gas Optimization: {{suggestions}}

  Critical Findings: {{count}}
  High Findings: {{count}}
  Medium Findings: {{count}}
  Low/Info Findings: {{count}}
```

---

## RULES

- NEVER store private keys, mnemonics, or API keys in source code — use `.env` + `.gitignore`
- ALWAYS follow Check-Effects-Interactions pattern on functions with external calls
- ALWAYS use `nonReentrant` modifier on functions that transfer ETH or call external contracts
- ALWAYS use `SafeERC20` for token transfers — bare `transfer()` can silently fail
- ALWAYS use custom errors instead of `require` strings — saves deployment and runtime gas
- ALWAYS check Chainlink oracle staleness — stale prices can drain protocols
- ALWAYS use two-step ownership transfer (`Ownable2Step`) for critical contracts
- ALWAYS add `_disableInitializers()` in constructors of upgradeable contracts
- NEVER reorder or remove storage variables in upgradeable contracts
- NEVER use `tx.origin` for authorization — use `msg.sender`
- NEVER use `transfer()` or `send()` for ETH — use `call{value: amount}("")` with reentrancy guard
- NEVER hardcode addresses — use HelperConfig pattern for multi-network support
- Run both Aderyn AND Slither before any deployment — they catch different issues
- Pin Solidity version (`pragma solidity 0.8.20;`) — never use floating (`^0.8.0`) in production
- Test coverage must include: unit, fuzz, and invariant tests before audit
